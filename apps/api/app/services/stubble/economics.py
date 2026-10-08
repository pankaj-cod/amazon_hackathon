from __future__ import annotations

import os

HA_PER_ACRE = 0.404686
C_TO_CO2 = 44.0 / 12.0

# Paddy straw dry matter left after combine harvest in Punjab/Haryana (t/ha).
STRAW_T_PER_HA = (5.5, 7.5)
# IPCC 2006 Vol.4 Table 2.6: combustion factor for rice residue.
COMBUSTION_FACTOR = 0.80
# IPCC 2006 Vol.4 Table 2.5 (agricultural residues), g per kg dry matter burned.
EF_CO2_G_PER_KG = 1515.0
EF_CH4_G_PER_KG = 2.7
EF_N2O_G_PER_KG = 0.07
# Published rice-straw open-burning PM2.5 emission factors span roughly this range.
EF_PM25_G_PER_KG = (6.0, 12.0)
# IPCC AR6 100-year GWP (CH4 non-fossil).
GWP_CH4 = 27.0
GWP_N2O = 273.0

# ICAR/PAU figures quoted in MoA&FW crop-residue guidance: kg lost per tonne of
# paddy straw burned. Low case assumes half stays in the ash on the field.
NUTRIENT_LOSS_KG_PER_T = {"N": 5.5, "P2O5": 2.3, "K2O": 25.0, "S": 1.2}
NUTRIENT_LOSS_SHARE = (0.5, 1.0)
# Rs per kg nutrient from subsidised MRP: urea Rs 266.5/45 kg (46 % N),
# DAP Rs 1350/50 kg (46 % P2O5), MOP ~Rs 1655/50 kg (60 % K2O).
NUTRIENT_PRICE_INR_PER_KG = {"N": 12.9, "P2O5": 58.7, "K2O": 55.2}

# Topsoil organic-carbon gain from retaining instead of burning residue in
# rice-wheat systems (long-term Indo-Gangetic Plain trials), t C/ha/yr.
SOC_GAIN_T_C_PER_HA_YR = (0.15, 0.50)

# Voluntary-market assumptions for an aggregated smallholder project.
CREDIT_DEDUCTION = (0.40, 0.20)        # uncertainty + buffer pool (low case, high case)
CREDIT_PRICE_USD = (5.0, 15.0)
FARMER_SHARE = (0.50, 0.70)            # after aggregator, verification and registry costs
INR_PER_USD = float(os.getenv("INR_PER_USD", "88"))

BURN_WEIGHT = {"burned": 1.0}


def _rng(low: float, high: float, nd: int = 2) -> dict:
    return {"low": round(low, nd), "high": round(high, nd)}


def _non_co2_tco2e(dm_burned_t: float) -> float:
    kg = dm_burned_t * 1000
    return kg * (EF_CH4_G_PER_KG * GWP_CH4 + EF_N2O_G_PER_KG * GWP_N2O) / 1e6


def burn_impact_per_ha() -> dict:
    dm = [s * COMBUSTION_FACTOR for s in STRAW_T_PER_HA]
    nutrients = {
        k: _rng(dm[0] * v * NUTRIENT_LOSS_SHARE[0], dm[1] * v * NUTRIENT_LOSS_SHARE[1], 1)
        for k, v in NUTRIENT_LOSS_KG_PER_T.items()
    }
    value = [
        sum(dm[i] * NUTRIENT_LOSS_KG_PER_T[k] * NUTRIENT_LOSS_SHARE[i] * p for k, p in NUTRIENT_PRICE_INR_PER_KG.items())
        for i in (0, 1)
    ]
    return {
        "straw_burned_t": _rng(*dm, 1),
        "co2_t": _rng(*(d * EF_CO2_G_PER_KG / 1000 for d in dm), 1),
        "non_co2_tco2e": _rng(*(_non_co2_tco2e(d) for d in dm)),
        "pm25_kg": _rng(dm[0] * EF_PM25_G_PER_KG[0], dm[1] * EF_PM25_G_PER_KG[1], 0),
        "nutrients_lost_kg": nutrients,
        "nutrient_value_inr": _rng(*value, 0),
        "soil_carbon_foregone_t_c": _rng(*SOC_GAIN_T_C_PER_HA_YR),
    }


def scale(d: dict, factor: float) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, dict) and "low" in v:
            nd = 0 if k in ("pm25_kg", "nutrient_value_inr") else 2
            out[k] = _rng(v["low"] * factor, v["high"] * factor, nd)
        elif isinstance(v, dict):
            out[k] = scale(v, factor)
    return out


def seasons_burned_equivalent(history: list[dict]) -> float:
    return sum(
        BURN_WEIGHT.get(h["status"], h["burned_fraction"] if h["status"] == "partly_burned" else 0.0)
        for h in history
    )


def carbon_credit_estimate(area_ha: float, burning_baseline: bool) -> dict:
    non_co2 = [_non_co2_tco2e(s * COMBUSTION_FACTOR) if burning_baseline else 0.0 for s in STRAW_T_PER_HA]
    soc = [g * C_TO_CO2 for g in SOC_GAIN_T_C_PER_HA_YR]
    credits_per_ha = [(non_co2[i] + soc[i]) * (1 - CREDIT_DEDUCTION[i]) for i in (0, 1)]
    inr_per_ha = [credits_per_ha[i] * CREDIT_PRICE_USD[i] * FARMER_SHARE[i] * INR_PER_USD for i in (0, 1)]
    per_acre = [v * HA_PER_ACRE for v in inr_per_ha]
    return {
        "credits_t_co2e_per_acre_per_year": _rng(*(c * HA_PER_ACRE for c in credits_per_ha)),
        "income_inr_per_acre_per_year": _rng(*per_acre, 0),
        "income_inr_field_per_year": _rng(*(v * area_ha for v in inr_per_ha), 0),
        "includes_avoided_burning": burning_baseline,
        "assumptions": credit_assumptions(burning_baseline),
    }


def credit_assumptions(burning_baseline: bool) -> list[str]:
    a = [
        f"Paddy straw {STRAW_T_PER_HA[0]}-{STRAW_T_PER_HA[1]} t/ha dry matter, {int(COMBUSTION_FACTOR*100)}% burns (IPCC 2006).",
        f"Soil carbon gain from keeping straw in the field: {SOC_GAIN_T_C_PER_HA_YR[0]}-{SOC_GAIN_T_C_PER_HA_YR[1]} t C/ha/yr.",
        "CO2 from burning straw is biogenic and is not credited; only methane and nitrous oxide count (IPCC AR6 GWP: CH4 27, N2O 273).",
        f"{int(CREDIT_DEDUCTION[1]*100)}-{int(CREDIT_DEDUCTION[0]*100)}% of credits held back for uncertainty and buffer pool.",
        f"Credit price US${CREDIT_PRICE_USD[0]:.0f}-{CREDIT_PRICE_USD[1]:.0f} per tCO2e; farmer receives {int(FARMER_SHARE[0]*100)}-{int(FARMER_SHARE[1]*100)}% after aggregator and verification costs; Rs {INR_PER_USD:.0f}/USD.",
        "Income needs enrolment in a registered project (e.g. Verra VM0042 or Gold Standard) through an aggregator; individual small fields cannot sell credits alone.",
    ]
    if not burning_baseline:
        a.append("No recent burning detected, so avoided-burning emissions are not additional and are excluded; only the soil-carbon part is counted.")
    return a
