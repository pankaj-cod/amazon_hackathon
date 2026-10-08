from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Language = Literal["pa", "hi", "en"]


class ComputeDirectIn(BaseModel):
    geometry: Any = Field(description="GeoJSON Point (field pin) or Polygon/Feature (field boundary)")
    field_area_acres: Optional[float] = Field(default=None, gt=0, le=100, description="Required for pins; overrides polygon area if given")
    language: Language = "pa"
    years: Optional[list[int]] = Field(default=None, description="Kharif seasons to check; defaults to the last 7")

