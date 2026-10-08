from __future__ import annotations

import logging
import math
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from shapely.geometry import shape, mapping
from shapely.ops import transform as shp_transform

from .burn import SceneStack

log = logging.getLogger(__name__)

# Sentinel-2 L2A Cloud-Optimised GeoTIFFs in the AWS Open Data registry
# (s3://sentinel-cogs), indexed by the Element 84 Earth Search STAC API.
STAC_URL = os.getenv("STAC_URL", "https://earth-search.aws.element84.com/v1")
COLLECTION = "sentinel-2-l2a"
BANDS = ("red", "nir", "swir22", "scl")
SEASON_START = (10, 1)
SEASON_END = (11, 30)
MAX_SCENE_CLOUD = 40
PIXEL = 10.0
PAD_M = 20.0
PIN_HALF_SIDE_M = 25.0
READ_WORKERS = int(os.getenv("S2_READ_WORKERS", "64"))

for k, v in {
    "AWS_NO_SIGN_REQUEST": "YES",
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
    "GDAL_HTTP_MAX_RETRY": "3",
    "GDAL_HTTP_RETRY_DELAY": "1",
    "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
    "GDAL_HTTP_MULTIPLEX": "YES",
    "GDAL_HTTP_VERSION": "2",
}.items():
    os.environ.setdefault(k, v)


def _utm_epsg(lon: float, lat: float) -> int:
    zone = int((lon + 180) // 6) + 1
    return (32600 if lat >= 0 else 32700) + zone


class FieldGrid:
    """A fixed 10 m UTM grid around the field so every scene lines up pixel for pixel."""

    def __init__(self, geometry: dict):
        geom = shape(geometry)
        c = geom.centroid
        self.lon, self.lat = c.x, c.y
        self.crs = f"EPSG:{_utm_epsg(c.x, c.y)}"
        fwd = Transformer.from_crs("EPSG:4326", self.crs, always_xy=True).transform
        g_utm = shp_transform(fwd, geom)
        if g_utm.geom_type == "Point":
            g_utm = g_utm.buffer(PIN_HALF_SIDE_M, cap_style=3)
        self.geom_utm = g_utm

        minx, miny, maxx, maxy = g_utm.bounds
        minx = math.floor((minx - PAD_M) / PIXEL) * PIXEL
        miny = math.floor((miny - PAD_M) / PIXEL) * PIXEL
        maxx = math.ceil((maxx + PAD_M) / PIXEL) * PIXEL
        maxy = math.ceil((maxy + PAD_M) / PIXEL) * PIXEL
        self.width = int((maxx - minx) / PIXEL)
        self.height = int((maxy - miny) / PIXEL)
        self.transform = from_origin(minx, maxy, PIXEL, PIXEL)
        self.mask = ~geometry_mask(
            [mapping(g_utm)], out_shape=(self.height, self.width),
            transform=self.transform, all_touched=False,
        )
        if not self.mask.any():
            self.mask = ~geometry_mask(
                [mapping(g_utm)], out_shape=(self.height, self.width),
                transform=self.transform, all_touched=True,
            )
        inv = Transformer.from_crs(self.crs, "EPSG:4326", always_xy=True).transform
        x0, y0 = inv(minx, miny)
        x1, y1 = inv(maxx, maxy)
        self.bbox_wgs84 = [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def search_season(bbox: list[float], year: int) -> list:
    from pystac_client import Client

    start = date(year, *SEASON_START).isoformat()
    end = date(year, *SEASON_END).isoformat()
    items = Client.open(STAC_URL).search(
        collections=[COLLECTION], bbox=bbox, datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": MAX_SCENE_CLOUD}}, max_items=60,
    ).items()
    best: dict[date, object] = {}
    for it in items:
        d = it.datetime.date()
        cc = it.properties.get("eo:cloud_cover", 100)
        if d not in best or cc < best[d].properties.get("eo:cloud_cover", 100):
            best[d] = it
    return [best[d] for d in sorted(best)]


def _read_band(href: str, grid: FieldGrid, resampling: Resampling) -> np.ndarray:
    with rasterio.open(href) as src:
        with WarpedVRT(src, crs=grid.crs, transform=grid.transform,
                       width=grid.width, height=grid.height, resampling=resampling) as vrt:
            return vrt.read(1)


def _read_job(item, band: str, grid: FieldGrid) -> np.ndarray | None:
    try:
        rs = Resampling.nearest if band == "scl" else Resampling.bilinear
        arr = _read_band(item.assets[band].href, grid, rs)
        return arr if band == "scl" else arr.astype(np.float32) / 10000.0
    except Exception as e:  # one bad scene must not sink the season
        log.warning("Skipping %s/%s: %s", getattr(item, "id", "?"), band, e)
        return None


def fetch_season_stacks(geometry: dict, years: list[int]) -> tuple[FieldGrid, dict[int, SceneStack]]:
    grid = FieldGrid(geometry)
    with ThreadPoolExecutor(min(8, len(years))) as ex:
        searched = dict(zip(years, ex.map(lambda y: search_season(grid.bbox_wgs84, y), years)))

    jobs = [(y, it, b) for y, items in searched.items() for it in items for b in BANDS]
    with ThreadPoolExecutor(READ_WORKERS) as ex:
        arrays = list(ex.map(lambda j: _read_job(j[1], j[2], grid), jobs))

    by_item: dict[tuple[int, str], dict] = {}
    for (y, it, b), arr in zip(jobs, arrays):
        entry = by_item.setdefault((y, it.id), {"date": it.datetime.date()})
        entry[b] = arr

    stacks: dict[int, SceneStack] = {}
    for y in years:
        scenes = [
            (e["date"], e) for (yy, _), e in by_item.items()
            if yy == y and all(e.get(b) is not None for b in BANDS) and (e["scl"] > 0).any()
        ]
        if not scenes:
            empty = np.zeros((0, grid.height, grid.width), np.float32)
            stacks[y] = SceneStack([], empty, empty, empty, empty, grid.mask)
            continue
        stacks[y] = SceneStack(
            dates=[d for d, _ in scenes],
            red=np.stack([s["red"] for _, s in scenes]),
            nir=np.stack([s["nir"] for _, s in scenes]),
            swir22=np.stack([s["swir22"] for _, s in scenes]),
            scl=np.stack([s["scl"] for _, s in scenes]),
            field_mask=grid.mask,
        )
    return grid, stacks
