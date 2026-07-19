"""
Pydantic Schemas for Match Telemetry & Fixtures.
"""
from typing import Optional

from pydantic import BaseModel, Field


class MatchCenterOut(BaseModel):
    id: int = Field(..., description="Match record ID")
    home_team: str = Field(..., description="Home team national name")
    home_flag: str = Field(..., description="Home team flag emoji")
    home_score: int = Field(..., description="Home team score")
    away_team: str = Field(..., description="Away team national name")
    away_flag: str = Field(..., description="Away team flag emoji")
    away_score: int = Field(..., description="Away team score")
    match_minute: str = Field(..., description="Live match minute indicator")
    is_live: bool = Field(..., description="Whether match is currently live")
    possession_home: int = Field(..., description="Home team possession percentage")
    possession_away: int = Field(..., description="Away team possession percentage")
    shots_home: int = Field(..., description="Home team shots on goal")
    shots_away: int = Field(..., description="Away team shots on goal")
    pass_accuracy_home: int = Field(..., description="Home team pass accuracy percentage")
    pass_accuracy_away: int = Field(..., description="Away team pass accuracy percentage")
    attendance: str = Field(..., description="Live spectator attendance count")
    stadium_capacity_pct: float = Field(..., description="Stadium capacity utilization percentage")

    class Config:
        from_attributes = True


class MatchFixtureOut(BaseModel):
    id: int = Field(..., description="Fixture record ID")
    date_label: str = Field(..., description="Fixture date and local kickoff time")
    teams: str = Field(..., description="Competing national teams")
    stage: str = Field(..., description="Tournament stage")

    class Config:
        from_attributes = True


class MatchUpdateReq(BaseModel):
    home_score: Optional[int] = Field(None, ge=0, description="Updated home score")
    away_score: Optional[int] = Field(None, ge=0, description="Updated away score")
    match_minute: Optional[str] = Field(None, description="Updated match minute string")
    possession_home: Optional[int] = Field(None, ge=0, le=100, description="Updated home possession %")
