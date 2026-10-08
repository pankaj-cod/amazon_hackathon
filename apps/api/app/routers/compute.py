import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Response

from app.schemas import ComputeDirectIn, VoiceIn
from app.services.stubble import voice
from app.services.stubble.service import FieldInputError, analyze_field

log = logging.getLogger(__name__)
router = APIRouter(tags=["stubble"])


@router.post("/compute/direct")
def compute_direct(payload: ComputeDirectIn) -> Any:
    if payload.years and (len(payload.years) > 10 or min(payload.years) < 2017):
        raise HTTPException(status_code=422, detail="years must be 10 or fewer seasons from 2017 onwards")
    try:
        return analyze_field(
            payload.geometry,
            area_acres=payload.field_area_acres,
            language=payload.language,
            years=sorted(set(payload.years)) if payload.years else None,
        )
    except FieldInputError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except (ValueError, TypeError, KeyError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid geometry: {e}")
    except Exception:
        log.exception("Field analysis failed")
        raise HTTPException(status_code=502, detail="Satellite data service unavailable, please try again")


@router.post("/advice/voice", response_class=Response)
def advice_voice(payload: VoiceIn) -> Response:
    if not voice.supported(payload.language):
        raise HTTPException(status_code=400, detail="Voice is available in Hindi and English only")
    try:
        audio = voice.synthesize(payload.text, payload.language)
    except Exception:
        log.exception("Polly synthesis failed")
        raise HTTPException(status_code=503, detail="Voice service unavailable")
    return Response(content=audio, media_type="audio/mpeg")
