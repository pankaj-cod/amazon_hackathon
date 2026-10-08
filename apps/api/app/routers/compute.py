import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas import ComputeDirectIn
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

