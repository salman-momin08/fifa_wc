"""
Match Telemetry Router.

Provides real-time dynamic match telemetry endpoints for live scores, possession,
shots on goal, pass accuracy, stadium capacity, and upcoming matchday schedules.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.constants import (
    DEFAULT_AWAY_FLAG,
    DEFAULT_AWAY_TEAM,
    DEFAULT_HOME_FLAG,
    DEFAULT_HOME_TEAM,
    DEFAULT_MATCH_MINUTE,
)
from app.database import MatchCenter, MatchFixture, get_db
from app.repositories.stadium import StadiumRepository
from app.schemas.match import MatchCenterOut, MatchFixtureOut, MatchUpdateReq
from app.services.match_simulator import MatchSimulator
from app.api.ws import manager

router = APIRouter()


@router.get("/live", response_model=MatchCenterOut)
def get_live_match(db: Session = Depends(get_db)) -> MatchCenterOut:
    """Retrieve live match telemetry computed dynamically by MatchSimulator.

    Returns current scores, ticking minutes, possession %, shots, and stadium capacity.

    Args:
        db: Database session dependency.

    Returns:
        MatchCenterOut instance with complete live telemetry.

    Raises:
        HTTPException: 500 if match telemetry calculation fails.
    """
    try:
        match = db.query(MatchCenter).first()
        if not match:
            match = MatchCenter(
                home_team=DEFAULT_HOME_TEAM,
                home_flag=DEFAULT_HOME_FLAG,
                home_score=2,
                away_team=DEFAULT_AWAY_TEAM,
                away_flag=DEFAULT_AWAY_FLAG,
                away_score=1,
                match_minute=DEFAULT_MATCH_MINUTE,
                is_live=True,
            )
            db.add(match)
            db.commit()
            db.refresh(match)

        telemetry = MatchSimulator.get_dynamic_telemetry(match)
        return MatchCenterOut(**telemetry)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate match telemetry: {str(exc)}",
        ) from exc


@router.get("/fixtures", response_model=List[MatchFixtureOut])
def get_match_fixtures(db: Session = Depends(get_db)) -> List[MatchFixtureOut]:
    """Retrieve list of upcoming stadium matchday fixtures.

    Args:
        db: Database session dependency.

    Returns:
        List of MatchFixtureOut instances.

    Raises:
        HTTPException: 500 if fixture query fails.
    """
    try:
        fixtures = db.query(MatchFixture).all()
        if not fixtures:
            fixtures = [
                MatchFixture(
                    date_label="Tomorrow - 18:00 Local",
                    teams="🇲🇽 Mexico vs 🇦🇷 Argentina",
                    stage="Matchday 2 - Group Stage",
                ),
                MatchFixture(
                    date_label="July 16 - 20:00 Local",
                    teams="🇫🇷 France vs 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England",
                    stage="Matchday 3 - Group Stage",
                ),
                MatchFixture(
                    date_label="July 18 - 17:00 Local",
                    teams="🇧🇷 Brazil vs 🇪🇸 Spain",
                    stage="Round of 32",
                ),
            ]
            for f in fixtures:
                db.add(f)
            db.commit()
            fixtures = db.query(MatchFixture).all()
        return [MatchFixtureOut.model_validate(f) for f in fixtures]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch match fixtures: {str(exc)}",
        ) from exc


@router.post("/update", response_model=MatchCenterOut)
async def update_match_live(req: MatchUpdateReq, db: Session = Depends(get_db)) -> MatchCenterOut:
    """Update live match telemetry and broadcast real-time state change via WebSockets.

    Args:
        req: MatchUpdateReq payload (optional home_score, away_score, match_minute).
        db: Database session dependency.

    Returns:
        Updated MatchCenterOut instance.

    Raises:
        HTTPException: 500 if match update or broadcast fails.
    """
    try:
        match = db.query(MatchCenter).first()
        if not match:
            match = MatchCenter(
                home_team=DEFAULT_HOME_TEAM,
                home_flag=DEFAULT_HOME_FLAG,
                home_score=2,
                away_team=DEFAULT_AWAY_TEAM,
                away_flag=DEFAULT_AWAY_FLAG,
                away_score=1,
                match_minute=DEFAULT_MATCH_MINUTE,
                is_live=True,
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

        await manager.broadcast({"type": "match_update", **telemetry})

        return MatchCenterOut(**telemetry)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update match telemetry: {str(exc)}",
        ) from exc
