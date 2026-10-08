from __future__ import annotations

import json
import logging
import os

from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

LANGUAGES = {"pa": "Punjabi (Gurmukhi script)", "hi": "Hindi (Devanagari script)", "en": "simple English"}
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-opus-5-5")
BEDROCK_REGION = os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-west-2"))
ADVICE_MODE = os.getenv("ADVICE_MODE", "bedrock")  # bedrock | template


class Advice(BaseModel):
    headline: str = Field(min_length=1)
    steps: list[str]
    money_note: str = Field(min_length=1)


SYSTEM_PROMPT = """You are a crop-residue extension officer helping rice-wheat farmers in Punjab and Haryana stop burning paddy stubble.
You receive satellite-derived facts about one farmer's field and write short, respectful advice the farmer can act on this season.

Rules:
- Write entirely in the requested language and script; keep machine names (Happy Seeder, Super Seeder, Smart Seeder, Super SMS, mulcher, baler) as farmers say them.
- Use only numbers given in the facts. Do not invent prices, phone numbers, deadlines or schemes.
- The only scheme you may mention is the Crop Residue Management (CRM) scheme: up to 50% subsidy on machines for individual farmers and up to 80% for cooperatives and Custom Hiring Centres.
- If burning was detected, be direct but never accusatory. If the data was unclear, say so honestly.
- Suggest in-field options first (Super SMS on the combine, Happy/Super/Smart Seeder sowing into residue, mulching and ploughing in with PUSA decomposer), then baling for biomass or biogas plants.
- Carbon credits are a small bonus that needs an aggregator project; the bigger gain is fertiliser and soil health kept in the field.

Reply with only a JSON object, no other text:
{"headline": "<one sentence on what the satellite saw>", "steps": ["<3 to 5 steps, each under 25 words>"], "money_note": "<one or two sentences on money lost to burning and possible carbon-credit income>"}"""


TEMPLATES = {
    "pa": {
        "burned": "ਤੁਹਾਡੇ ਖੇਤ ਵਿੱਚ ਪਿਛਲੇ {n} ਸੀਜ਼ਨਾਂ ਵਿੱਚੋਂ {b} ਵਾਰ ਪਰਾਲੀ ਸਾੜੀ ਗਈ ਲੱਗਦੀ ਹੈ।",
        "clean": "ਸ਼ਾਬਾਸ਼! ਪਿਛਲੇ {n} ਸੀਜ਼ਨਾਂ ਵਿੱਚ ਤੁਹਾਡੇ ਖੇਤ ਵਿੱਚ ਪਰਾਲੀ ਸਾੜਨ ਦਾ ਕੋਈ ਸਾਫ਼ ਨਿਸ਼ਾਨ ਨਹੀਂ ਮਿਲਿਆ।",
        "unclear": "ਬੱਦਲਾਂ ਕਾਰਨ ਤੁਹਾਡੇ ਖੇਤ ਦੀਆਂ ਸਾਫ਼ ਤਸਵੀਰਾਂ ਘੱਟ ਮਿਲੀਆਂ, ਇਸ ਲਈ ਨਤੀਜਾ ਪੱਕਾ ਨਹੀਂ ਹੈ।",
        "steps": [
            "ਪਰਾਲੀ ਨੂੰ ਅੱਗ ਨਾ ਲਾਓ — ਹੈਪੀ ਸੀਡਰ, ਸੁਪਰ ਸੀਡਰ ਜਾਂ ਸਮਾਰਟ ਸੀਡਰ ਨਾਲ ਪਰਾਲੀ ਵਿੱਚ ਹੀ ਕਣਕ ਦੀ ਸਿੱਧੀ ਬਿਜਾਈ ਕਰੋ।",
            "ਕੰਬਾਈਨ 'ਤੇ ਸੁਪਰ SMS ਲਗਵਾਓ ਤਾਂ ਜੋ ਪਰਾਲੀ ਖੇਤ ਵਿੱਚ ਬਰਾਬਰ ਖਿੱਲਰ ਜਾਵੇ।",
            "ਜਾਂ ਮਲਚਰ ਅਤੇ ਉਲਟਾਵੇਂ ਹਲ ਨਾਲ ਪਰਾਲੀ ਮਿੱਟੀ ਵਿੱਚ ਮਿਲਾਓ; PUSA ਡੀਕੰਪੋਜ਼ਰ ਦਾ ਛਿੜਕਾਅ ਪਰਾਲੀ ਗਾਲਣ ਵਿੱਚ ਮਦਦ ਕਰਦਾ ਹੈ।",
            "ਮਸ਼ੀਨ ਨਹੀਂ ਹੈ ਤਾਂ ਕਸਟਮ ਹਾਇਰਿੰਗ ਸੈਂਟਰ ਤੋਂ ਕਿਰਾਏ 'ਤੇ ਲਓ। CRM ਸਕੀਮ ਹੇਠ ਕਿਸਾਨ ਨੂੰ 50% ਅਤੇ ਸਹਿਕਾਰੀ ਸਭਾ ਨੂੰ 80% ਤੱਕ ਸਬਸਿਡੀ ਮਿਲਦੀ ਹੈ।",
            "ਬੇਲਰ ਨਾਲ ਪਰਾਲੀ ਦੀਆਂ ਗੰਢਾਂ ਬਣਵਾ ਕੇ ਬਾਇਓਮਾਸ ਜਾਂ ਬਾਇਓ-ਗੈਸ ਪਲਾਂਟ ਨੂੰ ਵੇਚੋ।",
        ],
        "money": "ਪਰਾਲੀ ਸਾੜਨ ਨਾਲ ਪ੍ਰਤੀ ਏਕੜ ਲਗਭਗ ₹{nv_low}–₹{nv_high} ਦੀ ਖਾਦ (N, P, K) ਸੜ ਜਾਂਦੀ ਹੈ। ਨਾ ਸਾੜਨ 'ਤੇ ਕਾਰਬਨ ਕ੍ਰੈਡਿਟ ਤੋਂ ਪ੍ਰਤੀ ਏਕੜ ਸਾਲਾਨਾ ₹{c_low}–₹{c_high} ਵਾਧੂ ਮਿਲ ਸਕਦੇ ਹਨ।",
    },
    "hi": {
        "burned": "आपके खेत में पिछले {n} सीज़न में से {b} बार पराली जलाई गई लगती है।",
        "clean": "शाबाश! पिछले {n} सीज़न में आपके खेत में पराली जलाने का कोई साफ़ निशान नहीं मिला।",
        "unclear": "बादलों के कारण आपके खेत की साफ़ तस्वीरें कम मिलीं, इसलिए नतीजा पक्का नहीं है।",
        "steps": [
            "पराली में आग न लगाएँ — हैप्पी सीडर, सुपर सीडर या स्मार्ट सीडर से पराली में ही गेहूँ की सीधी बुवाई करें।",
            "कंबाइन पर सुपर SMS लगवाएँ ताकि पराली खेत में बराबर फैल जाए।",
            "या मल्चर और पलटने वाले हल से पराली मिट्टी में मिलाएँ; PUSA डीकंपोज़र का छिड़काव पराली गलाने में मदद करता है।",
            "मशीन नहीं है तो कस्टम हायरिंग सेंटर से किराए पर लें। CRM योजना में किसान को 50% और सहकारी समिति को 80% तक सब्सिडी मिलती है।",
            "बेलर से पराली की गांठें बनवाकर बायोमास या बायो-गैस प्लांट को बेचें।",
        ],
        "money": "पराली जलाने से प्रति एकड़ लगभग ₹{nv_low}–₹{nv_high} की खाद (N, P, K) जल जाती है। न जलाने पर कार्बन क्रेडिट से प्रति एकड़ सालाना ₹{c_low}–₹{c_high} अतिरिक्त मिल सकते हैं।",
    },
    "en": {
        "burned": "Satellite images suggest stubble was burned on your field in {b} of the last {n} seasons.",
        "clean": "Well done! No clear sign of stubble burning on your field in the last {n} seasons.",
        "unclear": "Clouds limited clear satellite images of your field, so this result is uncertain.",
        "steps": [
            "Do not burn the straw — sow wheat directly into it with a Happy Seeder, Super Seeder or Smart Seeder.",
            "Fit a Super SMS on the combine so straw is spread evenly across the field.",
            "Or mulch and plough the straw in; a PUSA decomposer spray helps it break down faster.",
            "No machine? Rent one from a Custom Hiring Centre. The CRM scheme gives up to 50% subsidy to farmers and 80% to cooperatives.",
            "Get the straw baled and sell the bales to a biomass or biogas plant.",
        ],
        "money": "Burning destroys about ₹{nv_low}–₹{nv_high} of fertiliser (N, P, K) per acre. Not burning could add ₹{c_low}–₹{c_high} per acre per year from carbon credits.",
    },
}


def _fmt_inr(x: float) -> str:
    return f"{int(round(x)):,}"


def template_advice(facts: dict, lang: str) -> dict:
    t = TEMPLATES[lang]
    n, b = facts["seasons_checked"], facts["seasons_burned"]
    if b > 0:
        headline = t["burned"].format(n=n, b=b)
    elif facts["seasons_clear_enough"] < max(1, n // 2):
        headline = t["unclear"]
    else:
        headline = t["clean"].format(n=n)
    money = t["money"].format(
        nv_low=_fmt_inr(facts["nutrient_value_inr_per_acre_per_burn"]["low"]),
        nv_high=_fmt_inr(facts["nutrient_value_inr_per_acre_per_burn"]["high"]),
        c_low=_fmt_inr(facts["carbon_credit_inr_per_acre_per_year"]["low"]),
        c_high=_fmt_inr(facts["carbon_credit_inr_per_acre_per_year"]["high"]),
    )
    return {"language": lang, "headline": headline, "steps": t["steps"], "money_note": money, "source": "template"}


def _bedrock_advice(facts: dict, lang: str) -> dict:
    from anthropic import AnthropicBedrockMantle

    client = AnthropicBedrockMantle(aws_region=BEDROCK_REGION, timeout=30.0, max_retries=1)
    # Claude in Amazon Bedrock does not support structured outputs, so the JSON
    # shape is requested in the prompt and validated here.
    response = client.messages.create(
        model=BEDROCK_MODEL_ID,
        max_tokens=4000,
        output_config={"effort": "low"},
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Write the advice in {LANGUAGES[lang]}.\n\nField facts (JSON):\n{json.dumps(facts, ensure_ascii=False, indent=1)}",
        }],
    )
    if response.stop_reason != "end_turn":
        raise RuntimeError(f"Bedrock advice incomplete: stop_reason={response.stop_reason}")
    text = next((b.text for b in response.content if b.type == "text"), "")
    advice = Advice.model_validate_json(text[text.find("{"): text.rfind("}") + 1])
    if not 3 <= len(advice.steps) <= 6:
        raise ValueError(f"unexpected step count {len(advice.steps)}")
    return {
        "language": lang,
        "headline": advice.headline,
        "steps": advice.steps[:5],
        "money_note": advice.money_note,
        "source": "bedrock",
    }


def generate_advice(facts: dict, lang: str) -> dict:
    if lang not in LANGUAGES:
        lang = "pa"
    if ADVICE_MODE == "bedrock":
        try:
            return _bedrock_advice(facts, lang)
        except Exception as e:
            log.warning("Bedrock advice failed, using template: %s", e)
    return template_advice(facts, lang)
