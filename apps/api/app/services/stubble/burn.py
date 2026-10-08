from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date

import numpy as np

# Sentinel-2 Scene Classification: 4 = vegetation, 5 = bare soil.
CLEAR_SCL = (4, 5)

# Thresholds calibrated on Sentinel-2 L2A over rice-wheat fields in Sangrur,
# Punjab (Oct-Nov 2023): fresh char is dark in red and NIR with SWIR2 > NIR,
# while tilled/irrigated soil after sowing stays brighter in red.
CHAR_MAX_RED = 0.125
CHAR_MAX_NIR = 0.16
CHAR_MAX_NBR = -0.08
CHAR_MIN_SWIR2_RED_RATIO = 1.55
PRE_BURN_MIN_NBR = 0.05
MAX_DAYS_SINCE_PREVIOUS = 20
# Active flames saturate SWIR2 (0.6-1.6 observed); bright soil peaks near 0.44.
FIRE_MIN_SWIR2 = 0.55
FIRE_MIN_SWIR2_MINUS_NIR = 0.20

HARVEST_MAX_NBR = 0.20
MIN_CLEAR_FRACTION = 0.6
MIN_CLEAR_OBSERVATIONS = 3
BURNED_FRACTION = 0.30
PARTLY_BURNED_FRACTION = 0.10


@dataclass
class SceneStack:
    dates: list[date]
    red: np.ndarray      # (T, H, W) surface reflectance 0-1
    nir: np.ndarray
    swir22: np.ndarray
    scl: np.ndarray      # (T, H, W) integer class
    field_mask: np.ndarray  # (H, W) True inside field


@dataclass
class SeasonResult:
    year: int
    status: str  # burned | partly_burned | not_burned | no_harvest | no_data
    burned_fraction: float
    burn_date: str | None
    active_fire_seen: bool
    clear_observations: int
    max_gap_days: int | None
    confidence: str  # high | medium | low

    def to_dict(self) -> dict:
        return asdict(self)


def _nbr(nir: np.ndarray, swir22: np.ndarray) -> np.ndarray:
    denom = nir + swir22
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(denom > 0, (nir - swir22) / denom, np.nan)


def detect_season(year: int, stack: SceneStack) -> SeasonResult:
    mask = stack.field_mask
    n_field = int(mask.sum())
    if n_field == 0 or not stack.dates:
        return SeasonResult(year, "no_data", 0.0, None, False, 0, None, "low")

    order = np.argsort([d.toordinal() for d in stack.dates])
    dates = [stack.dates[i] for i in order]
    red, nir, sw2, scl = (a[order] for a in (stack.red, stack.nir, stack.swir22, stack.scl))
    nbr = _nbr(nir, sw2)
    clear = np.isin(scl, CLEAR_SCL)

    shape = mask.shape
    prev_nbr = np.full(shape, np.nan)
    prev_day = np.full(shape, -10_000)
    ever_clear = np.zeros(shape, bool)
    burned = np.zeros(shape, bool)
    fire_seen = False
    burn_date: date | None = None
    clear_days: list[date] = []
    field_nbr_series: list[float] = []

    for t, d in enumerate(dates):
        day = d.toordinal()
        c = clear[t] & mask
        if c.sum() >= MIN_CLEAR_FRACTION * n_field:
            clear_days.append(d)
            field_nbr_series.append(float(np.nanmedian(nbr[t][c])))

        with np.errstate(divide="ignore", invalid="ignore"):
            swir_red = sw2[t] / np.maximum(red[t], 1e-3)
        char = (
            (red[t] < CHAR_MAX_RED)
            & (nir[t] < CHAR_MAX_NIR)
            & (nbr[t] < CHAR_MAX_NBR)
            & (swir_red > CHAR_MIN_SWIR2_RED_RATIO)
        )
        recent = (day - prev_day) <= MAX_DAYS_SINCE_PREVIOUS
        new_burn = c & char & recent & (prev_nbr > PRE_BURN_MIN_NBR)

        fire = mask & (sw2[t] > FIRE_MIN_SWIR2) & ((sw2[t] - nir[t]) > FIRE_MIN_SWIR2_MINUS_NIR)
        if fire.any():
            fire_seen = True
            new_burn |= fire

        newly = new_burn & ~burned
        if burn_date is None and (fire.any() or newly.sum() >= PARTLY_BURNED_FRACTION * n_field):
            burn_date = d
        burned |= new_burn

        ever_clear |= c
        prev_nbr = np.where(c, nbr[t], prev_nbr)
        prev_day = np.where(c, day, prev_day)

    observed = int(ever_clear.sum())
    frac = float(burned.sum() / observed) if observed else 0.0

    gaps = [(b - a).days for a, b in zip(clear_days, clear_days[1:])]
    max_gap = max(gaps) if gaps else None
    n_clear = len(clear_days)
    harvested = bool(field_nbr_series) and min(field_nbr_series) < HARVEST_MAX_NBR

    if frac >= BURNED_FRACTION or (fire_seen and frac >= PARTLY_BURNED_FRACTION):
        status = "burned"
    elif frac >= PARTLY_BURNED_FRACTION or fire_seen:
        status = "partly_burned"
    elif n_clear < MIN_CLEAR_OBSERVATIONS:
        status = "no_data"
    elif not harvested:
        status = "no_harvest"
    else:
        status = "not_burned"

    if status in ("burned", "partly_burned"):
        confidence = "high" if (frac >= 0.5 or fire_seen) else "medium"
    elif status == "no_data":
        confidence = "low"
    else:
        confidence = "high" if (n_clear >= 6 and (max_gap or 99) <= 15) else "medium" if n_clear >= 4 else "low"

    return SeasonResult(
        year=year,
        status=status,
        burned_fraction=round(frac, 3),
        burn_date=burn_date.isoformat() if burn_date else None,
        active_fire_seen=fire_seen,
        clear_observations=n_clear,
        max_gap_days=max_gap,
        confidence=confidence,
    )
