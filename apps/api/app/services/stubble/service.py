from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path

from shapely.geometry import shape

from app.utils.geo import clean_and_validate, normalize_geometry

from . import economics as econ
from .advice import generate_advice
from .burn import detect_season
from .satellite import fetch_season_stacks
from .soil import get_soil_carbon

log = logging.getLogger(__name__)

ANALYSIS_VERSION = "stubble-v1"
SEASONS = 7
MAX_FIELD_HA = 40.0
API_ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = Path(os.getenv("CACHE_DIR", API_ROOT / ".cache"))
SEED_CACHE_DIR = Path(os.getenv("SEED_CACHE_DIR", API_ROOT / "demo_cache"))
CACHE_BUCKET = os.getenv("CACHE_BUCKET", "")
BURN_STATUSES = ("burned", "partly_burned")

# Rough bounding box of Punjab + Haryana with a margin.
REGION_BBOX = (73.5, 27.4, 77.8, 32.6)


class FieldInputError(ValueError):
    pass


def default_years(today: date | None = None) -> list[int]:
    today = today or date.today()
    last = today.year if today.month == 12 else today.year - 1
    return list(range(last - SEASONS + 1, last + 1))


def _prepare_geometry(geometry_in, area_acres: float | None) -> tuple[dict, float, str]:
    geom = normalize_geometry(geometry_in)
    if not isinstance(geom, dict) or "type" not in geom:
        raise FieldInputError("geometry must be GeoJSON")
    if geom["type"] == "Point":
        lon, lat = geom["coordinates"][:2]
        g = {"type": "Point", "coordinates": [round(float(lon), 6), round(float(lat), 6)]}
        area_ha = (area_acres or 2.0) * econ.HA_PER_ACRE
        kind = "pin"
    else:
        poly, area_m2, _ = clean_and_validate(geom)
        g = json.loads(json.dumps(poly.__geo_interface__))
        area_ha = area_m2 / 10_000
        if area_acres:
            area_ha = area_acres * econ.HA_PER_ACRE
        kind = "polygon"
    if area_ha <= 0 or area_ha > MAX_FIELD_HA:
        raise FieldInputError(f"field area must be between 0 and {MAX_FIELD_HA:.0f} ha")
    c = shape(g).centroid
    if not (REGION_BBOX[0] <= c.x <= REGION_BBOX[2] and REGION_BBOX[1] <= c.y <= REGION_BBOX[3]):
        raise FieldInputError("this tool currently covers fields in Punjab and Haryana only")
    return g, area_ha, kind


def _cache_key(geometry: dict, years: list[int]) -> str:
    raw = json.dumps({"g": geometry, "y": years, "v": ANALYSIS_VERSION}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _cache_get(key: str) -> dict | None:
    for directory in (SEED_CACHE_DIR, CACHE_DIR):
        path = directory / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text())
    if CACHE_BUCKET:
        try:
            import boto3
            body = boto3.client("s3").get_object(Bucket=CACHE_BUCKET, Key=f"analyses/{key}.json")["Body"].read()
            data = json.loads(body)
            _cache_put_local(key, data)
            return data
        except Exception:
            return None
    return None


def _cache_put_local(key: str, data: dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (CACHE_DIR / f"{key}.json").write_text(json.dumps(data))
    except OSError as e:
        log.warning("Local cache write failed: %s", e)


def _cache_put(key: str, data: dict) -> None:
    _cache_put_local(key, data)
    if CACHE_BUCKET:
        try:
            import boto3
            boto3.client("s3").put_object(
                Bucket=CACHE_BUCKET, Key=f"analyses/{key}.json",
                Body=json.dumps(data).encode(), ContentType="application/json",
            )
        except Exception as e:
            log.warning("S3 cache write failed: %s", e)


def observe_field(geometry: dict, years: list[int]) -> dict:
    key = _cache_key(geometry, years)
    cached = _cache_get(key)
    if cached:
        return {**cached, "cached": True}
    grid, stacks = fetch_season_stacks(geometry, years)
    history = [detect_season(y, stacks[y]).to_dict() for y in years]
    soil = get_soil_carbon(grid.lon, grid.lat)
    data = {
        "burn_history": history,
        "soil": soil,
        "centroid": [round(grid.lon, 6), round(grid.lat, 6)],
        "field_pixels": int(grid.mask.sum()),
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }
    if any(h["clear_observations"] > 0 for h in history):
        _cache_put(key, data)
    return {**data, "cached": False}


def _summary(history: list[dict]) -> dict:
    burned = [h for h in history if h["status"] in BURN_STATUSES]
    return {
        "seasons_checked": len(history),
        "seasons_burned": len(burned),
        "seasons_unclear": sum(h["status"] == "no_data" for h in history),
        "last_burn_year": max((h["year"] for h in burned), default=None),
        "burned_season_equivalent": round(econ.seasons_burned_equivalent(history), 2),
    }


def analyze_field(geometry_in, area_acres: float | None = None, language: str = "pa",
                  years: list[int] | None = None) -> dict:
    geometry, area_ha, kind = _prepare_geometry(geometry_in, area_acres)
    years = years or default_years()
    obs = observe_field(geometry, years)
    history = obs["burn_history"]
    summary = _summary(history)

    per_ha = econ.burn_impact_per_ha()
    per_burn_field = econ.scale(per_ha, area_ha)
    cumulative = econ.scale(per_ha, area_ha * summary["burned_season_equivalent"])
    soc_stock = obs["soil"]["soc_stock_t_per_ha"]
    soc_lost_share = {
        k: round(100 * v * summary["burned_season_equivalent"] / soc_stock, 1) if soc_stock else None
        for k, v in per_ha["soil_carbon_foregone_t_c"].items()
    }

    recent = history[-3:]
    burning_baseline = any(h["status"] in BURN_STATUSES for h in recent)
    credits = econ.carbon_credit_estimate(area_ha, burning_baseline)

    area_acres_out = area_ha / econ.HA_PER_ACRE
    nutrient_per_acre = econ.scale({"v": per_ha["nutrient_value_inr"]}, econ.HA_PER_ACRE)["v"]
    facts = {
        "field_area_acres": round(area_acres_out, 2),
        "seasons_checked": summary["seasons_checked"],
        "seasons_burned": summary["seasons_burned"],
        "seasons_clear_enough": sum(h["status"] != "no_data" for h in history),
        "burn_years": [h["year"] for h in history if h["status"] in BURN_STATUSES],
        "last_burn_year": summary["last_burn_year"],
        "nutrient_value_inr_per_acre_per_burn": nutrient_per_acre,
        "soil_organic_carbon_t_per_ha": soc_stock,
        "soil_carbon_foregone_t_c_per_ha_total": econ.scale(
            {"v": per_ha["soil_carbon_foregone_t_c"]}, summary["burned_season_equivalent"])["v"],
        "pm25_kg_per_burn_field": per_burn_field["pm25_kg"],
        "carbon_credit_inr_per_acre_per_year": credits["income_inr_per_acre_per_year"],
        "carbon_credit_needs_aggregator": True,
    }

    return {
        "field": {
            "input_type": kind,
            "area_acres": round(area_acres_out, 2),
            "area_ha": round(area_ha, 3),
            "centroid": obs["centroid"],
        },
        "summary": summary,
        "burn_history": history,
        "soil": {**obs["soil"], "share_of_stock_lost_pct": soc_lost_share},
        "impact": {"per_burn": per_burn_field, "cumulative": cumulative},
        "carbon_credits": credits,
        "advice": generate_advice(facts, language),
        "data_sources": [
            "Sentinel-2 L2A surface reflectance, AWS Open Data Registry (Element 84 Earth Search STAC)",
            f"Soil organic carbon: {'ISRIC SoilGrids v2.0' if obs['soil']['source'] == 'soilgrids_v2' else 'regional default for Punjab/Haryana'}",
            "Emission factors: IPCC 2006 Vol.4 Ch.2; GWP: IPCC AR6",
        ],
        "cached": obs["cached"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
