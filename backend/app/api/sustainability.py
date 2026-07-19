from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.stadium import StadiumRepository
from app.services.sustainability import SustainabilityService
from app.services.llm import run_llm_chain

router = APIRouter()

@router.get("/nudge")
async def get_sustainability_nudge(
    gate: str = "Gate A",
    lang: str = "en",
    user_refills: int = 0,
    public_trans_used: bool = False,
    db: Session = Depends(get_db)
):
    repo = StadiumRepository(db)
    node = repo.get_wayfinding_node_by_name(gate)
    
    # 1. Fetch nearest green stations
    stations = SustainabilityService.get_refill_and_recycle_stations(gate)
    
    # 2. Calculate impact metrics
    impact = SustainabilityService.calculate_green_impact(user_refills, public_trans_used)
    
    if not node:
        node_features = "General stadium area with recycling containers."
    else:
        features_list = []
        if node.has_wheelchair_ramp:
            features_list.append("accessible routes")
        if node.restroom_nearby:
            features_list.append("water-efficient restroom sinks")
        if node.first_aid_nearby:
            features_list.append("eco-first-aid container recycling points")
        node_features = f"Zone: {node.zone}. Features near this gate: {', '.join(features_list) or 'recycling bins'}."

    system_prompt = (
        "You are the FIFA World Cup Green Initiative Assistant. "
        "Create a short, fun, and encouraging environmental nudge (1-2 sentences) "
        "tailored to the fan's location and available green features. Mention refill stations."
    )
    user_prompt = f"The fan is at {gate}. Features info: {node_features}. Nearest Refill Station: {stations['nearest_refill']}"
    
    nudge = await run_llm_chain(db, system_prompt, user_prompt, lang)
    
    return {
        "gate": gate,
        "nudge": nudge,
        "nearest_refill": stations["nearest_refill"],
        "nearest_recycle": stations["nearest_recycle"],
        "nearest_ev_shuttle": stations["nearest_ev_shuttle"],
        "impact": impact
    }
