"""
Pydantic Schemas for Sustainability Nudge & Green Score Engine.
"""
from pydantic import BaseModel, Field
from typing import Optional, List

class SustainabilityNudgeOut(BaseModel):
    nudge: str = Field(..., description="Location-aware sustainability recommendation")
    gate: str = Field(..., description="Target stadium gate or zone")
    language: str = Field(..., description="Target language code")
    green_score: int = Field(..., description="User calculated Green Score")
    plastic_saved_grams: int = Field(..., description="Estimated plastic saved in grams")
    co2_reduced_grams: int = Field(..., description="Estimated CO2 reduction in grams")
    badge: str = Field(..., description="Earned eco achievement badge")

    class Config:
        from_attributes = True

class SustainabilityActionReq(BaseModel):
    gate: str = Field(..., description="Gate or location of eco action")
    action_type: str = Field(..., description="Action type: water_refill, recycling, ev_shuttle, public_transit")
    count: Optional[int] = Field(1, ge=1, description="Number of actions logged")
