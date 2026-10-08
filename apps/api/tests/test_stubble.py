from datetime import date, timedelta

import numpy as np
import pytest

from app.services.stubble import economics as econ
from app.services.stubble.advice import template_advice
from app.services.stubble.burn import SceneStack, detect_season
from app.services.stubble.service import FieldInputError, _prepare_geometry, default_years

GREEN = (0.09, 0.30, 0.10)      # red, nir, swir22 for green paddy (NBR ~0.5)
STUBBLE = (0.25, 0.38, 0.27)    # harvested, unburned straw (NBR ~0.17)
CHAR = (0.095, 0.105, 0.19)     # fresh burn scar (NBR ~ -0.29)
SOIL = (0.14, 0.17, 0.22)       # tilled/irrigated soil after sowing (NBR ~ -0.13)
FIRE = (0.12, 0.20, 0.90)       # active flames saturating SWIR2


def make_stack(sequence, cloudy=(), shape=(6, 6)):
    start = date(2023, 10, 1)
    dates = [start + timedelta(days=5 * i) for i in range(len(sequence))]
    def band(i):
        return np.stack([np.full(shape, s[i], np.float32) for s in sequence])
    scl = np.full((len(sequence),) + shape, 4, np.uint8)
    for t in cloudy:
        scl[t] = 9
    return SceneStack(dates, band(0), band(1), band(2), scl, np.ones(shape, bool))


def test_burn_after_harvest_detected_with_date():
    r = detect_season(2023, make_stack([GREEN, GREEN, STUBBLE, CHAR, SOIL, SOIL]))
    assert r.status == "burned"
    assert r.burn_date == "2023-10-16"
    assert r.burned_fraction == 1.0


def test_harvest_then_tillage_is_not_a_burn():
    r = detect_season(2023, make_stack([GREEN, GREEN, STUBBLE, STUBBLE, SOIL, SOIL, SOIL]))
    assert r.status == "not_burned"


def test_dark_scene_after_long_gap_is_not_counted():
    seq = [GREEN, STUBBLE, STUBBLE, STUBBLE, STUBBLE, STUBBLE, CHAR]
    r = detect_season(2023, make_stack(seq, cloudy=(2, 3, 4, 5)))
    assert r.status != "burned"


def test_active_fire_marks_burn():
    r = detect_season(2023, make_stack([GREEN, STUBBLE, FIRE, SOIL, SOIL]))
    assert r.active_fire_seen
    assert r.status == "burned"


def test_cloudy_season_is_no_data():
    r = detect_season(2023, make_stack([GREEN, STUBBLE, STUBBLE, SOIL], cloudy=(1, 2, 3)))
    assert r.status == "no_data"
    assert r.confidence == "low"


def test_field_still_green_is_no_harvest():
    r = detect_season(2023, make_stack([GREEN] * 6))
    assert r.status == "no_harvest"


def test_non_co2_only_counts_methane_and_nitrous_oxide():
    per_ha = econ.burn_impact_per_ha()
    assert 0.3 < per_ha["non_co2_tco2e"]["low"] < per_ha["non_co2_tco2e"]["high"] < 0.7
    assert per_ha["co2_t"]["low"] > 5


def test_credit_range_is_ordered_and_drops_without_burning_baseline():
    with_burn = econ.carbon_credit_estimate(1.0, True)
    without = econ.carbon_credit_estimate(1.0, False)
    lo, hi = with_burn["income_inr_per_acre_per_year"].values()
    assert 0 < lo < hi
    assert without["income_inr_per_acre_per_year"]["high"] < hi
    assert any("not additional" in a for a in without["assumptions"])


def test_template_advice_in_all_languages():
    facts = {
        "seasons_checked": 7, "seasons_burned": 2, "seasons_clear_enough": 7,
        "nutrient_value_inr_per_acre_per_burn": {"low": 1412, "high": 3851},
        "carbon_credit_inr_per_acre_per_year": {"low": 51, "high": 714},
    }
    for lang in ("pa", "hi", "en"):
        a = template_advice(facts, lang)
        assert "2" in a["headline"] and "7" in a["headline"]
        assert "1,412" in a["money_note"]
        assert 3 <= len(a["steps"]) <= 5


def test_pin_outside_punjab_haryana_rejected():
    with pytest.raises(FieldInputError):
        _prepare_geometry({"type": "Point", "coordinates": [77.59, 12.97]}, 2)


def test_polygon_area_used_for_field():
    poly = {"type": "Polygon", "coordinates": [[[75.68, 30.16], [75.681, 30.16], [75.681, 30.161], [75.68, 30.161], [75.68, 30.16]]]}
    _, area_ha, kind = _prepare_geometry(poly, None)
    assert kind == "polygon"
    assert 1.0 < area_ha < 1.2


def test_default_years_excludes_running_season():
    assert default_years(date(2026, 10, 8)) == list(range(2019, 2026))
    assert default_years(date(2026, 12, 2))[-1] == 2026


class _FakeMessages:
    def __init__(self, text):
        self.text = text

    def create(self, **kwargs):
        from types import SimpleNamespace
        assert kwargs["model"].startswith("anthropic.")
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=self.text)])


def _fake_bedrock(monkeypatch, text):
    import anthropic

    class Fake:
        def __init__(self, **kwargs):
            self.messages = _FakeMessages(text)

    monkeypatch.setattr(anthropic, "AnthropicBedrockMantle", Fake)


FACTS = {
    "seasons_checked": 7, "seasons_burned": 1, "seasons_clear_enough": 7,
    "nutrient_value_inr_per_acre_per_burn": {"low": 1412, "high": 3851},
    "carbon_credit_inr_per_acre_per_year": {"low": 51, "high": 714},
}


def test_bedrock_json_reply_is_used(monkeypatch):
    from app.services.stubble import advice
    _fake_bedrock(monkeypatch, 'Here: {"headline": "H", "steps": ["a", "b", "c"], "money_note": "M"}')
    out = advice.generate_advice(FACTS, "hi")
    assert out["source"] == "bedrock" and out["steps"] == ["a", "b", "c"]


def test_bad_bedrock_reply_falls_back_to_template(monkeypatch):
    from app.services.stubble import advice
    _fake_bedrock(monkeypatch, "not json")
    out = advice.generate_advice(FACTS, "pa")
    assert out["source"] == "template"
