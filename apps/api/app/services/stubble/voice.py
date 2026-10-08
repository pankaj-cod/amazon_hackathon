from __future__ import annotations

import os

POLLY_REGION = os.getenv("POLLY_REGION", os.getenv("AWS_REGION", "us-west-2"))
# Amazon Polly has no Punjabi voice; Kajal (neural) speaks Hindi and Indian English.
VOICES = {"hi": ("Kajal", "hi-IN"), "en": ("Kajal", "en-IN")}


def supported(lang: str) -> bool:
    return lang in VOICES


def synthesize(text: str, lang: str) -> bytes:
    import boto3

    voice, code = VOICES[lang]
    polly = boto3.client("polly", region_name=POLLY_REGION)
    resp = polly.synthesize_speech(
        Text=text[:2900], OutputFormat="mp3", VoiceId=voice, Engine="neural", LanguageCode=code,
    )
    return resp["AudioStream"].read()
