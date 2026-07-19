from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class IncidentReport(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=5, max_length=1000)
    gate: str = Field(..., min_length=2, max_length=50)
    severity: str = Field(..., pattern="^(low|medium|high)$")

class IncidentApproval(BaseModel):
    incident_id: int
    custom_action: Optional[str] = Field(None, max_length=1000)

class IncidentOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    severity: str
    gate: str
    suggested_action: Optional[str]
    is_approved: bool
    timestamp: datetime

    class Config:
        from_attributes = True
