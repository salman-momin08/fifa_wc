from pydantic import BaseModel, Field
from typing import Optional

class CrowdSensorUpdate(BaseModel):
    zone: str = Field(..., min_length=2, max_length=50)
    density_percentage: int = Field(..., ge=0, le=100)
    advisory: Optional[str] = Field(None, max_length=500)

class CrowdSensorOut(BaseModel):
    zone: str
    density_percentage: int
    advisory: Optional[str]

    class Config:
        from_attributes = True
