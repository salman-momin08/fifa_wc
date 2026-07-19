from pydantic import BaseModel, Field
from typing import List, Optional

class AssistantRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Fan request or navigation query")
    lang: str = Field("en", min_length=2, max_length=5, description="Requested language")

class AssistantOut(BaseModel):
    response: str
    confidence: float
    sources: List[str]
    fallback_response: Optional[str] = None
