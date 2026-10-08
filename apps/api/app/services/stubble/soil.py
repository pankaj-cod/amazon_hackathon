from __future__ import annotations

import logging

import httpx

log = logging.getLogger(__name__)

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
LAYERS = (("0-5cm", 5), ("5-15cm", 10), ("15-30cm", 15))

# Typical Punjab/Haryana rice-wheat topsoil when SoilGrids is unreachable:
# ~0.45 % organic carbon, bulk density ~1.5 g/cm3.
FALLBACK_SOC_G_PER_KG = 4.5
FALLBACK_BULK_DENSITY = 1.5


def soc_stock_t_per_ha(soc_g_per_kg: float, bulk_density_g_cm3: float, thickness_cm: float) -> float:
    return soc_g_per_kg * bulk_density_g_cm3 * thickness_cm * 0.1


def _fallback() -> dict:
    return {
        "soc_g_per_kg": FALLBACK_SOC_G_PER_KG,
        "bulk_density_g_cm3": FALLBACK_BULK_DENSITY,
        "soc_stock_t_per_ha": round(soc_stock_t_per_ha(FALLBACK_SOC_G_PER_KG, FALLBACK_BULK_DENSITY, 30), 1),
        "depth": "0-30cm",
        "source": "regional_default",
    }


def get_soil_carbon(lon: float, lat: float, timeout: float = 10.0) -> dict:
    params = [("lon", lon), ("lat", lat), ("property", "soc"), ("property", "bdod"), ("value", "mean")]
    params += [("depth", d) for d, _ in LAYERS]
    try:
        r = httpx.get(SOILGRIDS_URL, params=params, timeout=timeout)
        r.raise_for_status()
        layers = {l["name"]: l for l in r.json()["properties"]["layers"]}
        values = {}
        for name in ("soc", "bdod"):
            factor = layers[name]["unit_measure"]["d_factor"]
            values[name] = {d["label"]: d["values"]["mean"] / factor for d in layers[name]["depths"]}
        stock = sum(soc_stock_t_per_ha(values["soc"][l], values["bdod"][l], t) for l, t in LAYERS)
        total = sum(t for _, t in LAYERS)
        return {
            "soc_g_per_kg": round(sum(values["soc"][l] * t for l, t in LAYERS) / total, 2),
            "bulk_density_g_cm3": round(sum(values["bdod"][l] * t for l, t in LAYERS) / total, 2),
            "soc_stock_t_per_ha": round(stock, 1),
            "depth": "0-30cm",
            "source": "soilgrids_v2",
        }
    except Exception as e:
        log.warning("SoilGrids unavailable, using regional default: %s", e)
        return _fallback()
