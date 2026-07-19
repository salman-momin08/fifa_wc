from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.transport import TransitAlertUpdate, TransitAlertOut
from app.repositories.stadium import StadiumRepository
from app.services.llm import run_llm_chain
from app.api.ws import manager

router = APIRouter()

@router.get("/status")
def get_transit_status(db: Session = Depends(get_db)):
    repo = StadiumRepository(db)
    alerts = repo.get_transit_alerts()
    return [{"route": a.route, "status": a.status, "delay_minutes": a.delay_minutes} for a in alerts]

@router.post("/update")
async def update_transit_status(req: TransitAlertUpdate, db: Session = Depends(get_db)):
    repo = StadiumRepository(db)
    
    # Prompt GenAI to format a clean transit advisory
    system_prompt = (
        "You are a Transportation Coordinator AI. Condense transit delay numbers and routes "
        "into a simplified, spectator-friendly summary notification. Be concise."
    )
    user_prompt = f"Transit Route: {req.route}, Status: {req.status}, Delay: {req.delay_minutes} minutes."
    
    summary = await run_llm_chain(db, system_prompt, user_prompt, req.lang)
    
    repo.create_or_update_transit_alert(req.route, req.status, req.delay_minutes)
    
    await manager.broadcast({
        "type": "transit_update",
        "route": req.route,
        "status": req.status,
        "delay_minutes": req.delay_minutes,
        "summary": summary
    })
    
    return {"message": "Transit status updated", "route": req.route, "summary": summary}
