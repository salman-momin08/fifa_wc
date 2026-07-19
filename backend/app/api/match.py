"""
Match Telemetry Router.
Provides real-time dynamic match telemetry endpoints for live scores, possession,
shots on goal, pass accuracy, stadium capacity, and upcoming matchday schedules.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db, MatchCenter, MatchFixture
from app.schemas.match import MatchCenterOut, MatchFixtureOut, MatchUpdateReq
from app.services.match_simulator import MatchSimulator
from app.api.ws import manager

router = APIRouter()


@router.get("/live", response_model=MatchCenterOut)
def get_live_match(db: Session = Depends(get_db)):
    """
    Retrieve live match telemetry computed dynamically by MatchSimulator.
    Returns current scores, ticking minutes, possession %, shots, and stadium capacity.
    """
    try:
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

        telemetry = MatchSimulator.get_dynamic_telemetry(match)
        return MatchCenterOut(**telemetry)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate match telemetry: {str(e)}"
        )

@router.get("/fixtures", response_model=List[MatchFixtureOut])
def get_match_fixtures(db: Session = Depends(get_db)):
    """
    Retrieve list of upcoming stadium matchday fixtures.
    """
    try:
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch match fixtures: {str(e)}"
        )

@router.post("/update", response_model=MatchCenterOut)
async def update_match_live(req: MatchUpdateReq, db: Session = Depends(get_db)):
    """
    Update live match telemetry and broadcast real-time state change via WebSockets.
    """
    try:
        match = db.query(MatchCenter).first()
        if not match:
            match = MatchCenter(
                home_team="CANADA", home_flag="🇨🇦", home_score=2,
                away_team="USA", away_flag="🇺🇸", away_score=1,
                match_minute="76'", is_live=True
            )
            db.add(match)

        if req.home_score is not None:
            match.home_score = req.home_score
        if req.away_score is not None:
            match.away_score = req.away_score
        if req.match_minute is not None:
            match.match_minute = req.match_minute
            
        db.commit()
        db.refresh(match)

        telemetry = MatchSimulator.get_dynamic_telemetry(match)

        # Broadcast update to connected clients via WebSocket manager
        await manager.broadcast({
            "type": "match_update",
            **telemetry
        })

        return MatchCenterOut(**telemetry)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update match telemetry: {str(e)}"
        )
