"""
Transport Coordination Router.

Aggregates transit delay bulletins (Subway/Metro, Shuttle Buses, Parking Express)
and broadcasts multilingual AI-generated advisories to connected fan clients.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.transport import TransitAlertUpdate, TransitAlertOut
from app.repositories.stadium import StadiumRepository
from app.services.llm import run_llm_chain
from app.api.ws import manager

router = APIRouter()


@router.get("/status", response_model=List[TransitAlertOut])
def get_transit_status(db: Session = Depends(get_db)) -> List[TransitAlertOut]:
    """Retrieve all active transit alerts and delay summaries.

    Returns:
        List of TransitAlertOut objects with route, status, and delay_minutes.
    """
    repo = StadiumRepository(db)
    alerts = repo.get_transit_alerts()
    return [TransitAlertOut(route=a.route, status=a.status, delay_minutes=a.delay_minutes) for a in alerts]


@router.post("/update")
async def update_transit_status(req: TransitAlertUpdate, db: Session = Depends(get_db)) -> dict:
    """Update a transit route status and broadcast an AI-generated multilingual advisory.

    Generates a concise spectator-friendly summary via Google Gemini before
    persisting the update and pushing a WebSocket broadcast to all clients.

    Args:
        req: Transit alert update payload (route, status, delay_minutes, lang).
        db: Database session dependency.

    Returns:
        Confirmation message, route name, delay_minutes, and AI-generated summary.

    Raises:
        HTTPException: 500 if transit update or broadcast fails.
    """
    repo = StadiumRepository(db)

    system_prompt = (
        "You are a Transportation Coordinator AI. Condense transit delay numbers and routes "
        "into a simplified, spectator-friendly summary notification. Be concise."
    )
    user_prompt = f"Transit Route: {req.route}, Status: {req.status}, Delay: {req.delay_minutes} minutes."

    try:
        summary = await run_llm_chain(db, system_prompt, user_prompt, req.lang)
        repo.create_or_update_transit_alert(req.route, req.status, req.delay_minutes)

        await manager.broadcast({
            "type": "transit_update",
            "route": req.route,
            "status": req.status,
            "delay_minutes": req.delay_minutes,
            "summary": summary,
        })

        return {"message": "Transit status updated", "route": req.route, "delay_minutes": req.delay_minutes, "summary": summary}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transit update failed: {str(exc)}") from exc
