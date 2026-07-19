"""
Pydantic Validation Schemas for Transport Alerts and Transit Status Updates.
"""
from typing import Optional

from pydantic import BaseModel, Field


class TransitAlertUpdate(BaseModel):
    route: str = Field(..., min_length=2, max_length=50)
    status: str = Field(..., min_length=2, max_length=20)
    delay_minutes: int = Field(0, ge=0, le=480)
    lang: str = Field("en", min_length=2, max_length=5)


class TransitAlertOut(BaseModel):
    route: str
    status: str
    delay_minutes: int

    class Config:
        from_attributes = True
