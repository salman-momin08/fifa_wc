"""
Pydantic Validation Schemas for Crowd Density Sensors and Advisories.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CrowdSensorUpdate(BaseModel):
    zone: str = Field(..., min_length=2, max_length=50)
    density_percentage: int = Field(..., ge=0, le=100)
    advisory: Optional[str] = Field(None, max_length=500)


class CrowdSensorOut(BaseModel):
    zone: str
    density_percentage: int
    advisory: Optional[str]

    model_config = ConfigDict(from_attributes=True)
