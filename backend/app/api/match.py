from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db, MatchCenter, MatchFixture
from app.services.match_simulator import MatchSimulator
from app.api.ws import manager

router = APIRouter()

class MatchCenterOut(BaseModel):
    id: int
    home_team: str
    home_flag: str
    home_score: int
    away_team: str
    away_flag: str
    away_score: int
    match_minute: str
    is_live: bool
    possession_home: int
    possession_away: int
    shots_home: int
    shots_away: int
    pass_accuracy_home: int
    pass_accuracy_away: int
    attendance: str
    stadium_capacity_pct: float

    class Config:
        from_attributes = True

class MatchFixtureOut(BaseModel):
    id: int
    date_label: str
    teams: str
    stage: str

    class Config:
        from_attributes = True

class MatchUpdateReq(BaseModel):
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    match_minute: Optional[str] = None
    possession_home: Optional[int] = None

@router.get("/live", response_model=MatchCenterOut)
def get_live_match(db: Session = Depends(get_db)):
    match = db.query(MatchCenter).first()
    if not match:
        match = MatchCenter(
            home_team="CANADA", home_flag="🇨🇦", home_score=2,
            away_team="USA", away_flag="🇺🇸", away_score=1,
            match_minute="76'", is_live=True
        )
        db.add(match)
        db.commit()
        db.refresh(match)
    
    # Calculate live telemetry dynamically (ticking minutes, possession, shots, attendance)
    telemetry = MatchSimulator.get_dynamic_telemetry(match)
    return AssistantOut_or_Dict(telemetry)

def AssistantOut_or_Dict(data: dict) -> MatchCenterOut:
    return MatchCenterOut(**data)

@router.get("/fixtures", response_model=List[MatchFixtureOut])
def get_match_fixtures(db: Session = Depends(get_db)):
    fixtures = db.query(MatchFixture).all()
    if not fixtures:
        fixtures = [
            MatchFixture(date_label="Tomorrow - 18:00 Local", teams="🇲🇽 Mexico vs 🇦🇷 Argentina", stage="Matchday 2 - Group Stage"),
            MatchFixture(date_label="July 16 - 20:00 Local", teams="🇫🇷 France vs 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England", stage="Matchday 3 - Group Stage"),
            MatchFixture(date_label="July 18 - 17:00 Local", teams="🇧🇷 Brazil vs 🇪🇸 Spain", stage="Round of 32")
        ]
        for f in fixtures:
            db.add(f)
        db.commit()
        fixtures = db.query(MatchFixture).all()
    return fixtures

@router.post("/update")
async def update_match_live(req: MatchUpdateReq, db: Session = Depends(get_db)):
    match = db.query(MatchCenter).first()
    if match:
        if req.home_score is not None:
            match.home_score = req.home_score
        if req.away_score is not None:
            match.away_score = req.away_score
        if req.match_minute is not None:
            match.match_minute = req.match_minute
        db.commit()
        db.refresh(match)

        telemetry = MatchSimulator.get_dynamic_telemetry(match)

        # Broadcast dynamic match update over WebSockets
        await manager.broadcast({
            "type": "match_update",
            **telemetry
        })

    return MatchSimulator.get_dynamic_telemetry(match)
