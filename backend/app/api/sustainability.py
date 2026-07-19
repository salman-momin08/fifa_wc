"""
Sustainability & Green Initiative Router.

Provides location-aware eco nudges, green impact metrics, and gamification
scores to encourage fans to reduce plastic waste and carbon emissions
throughout the FIFA World Cup 2026 tournament.
"""
from typing import Any, Dict

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
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return a location-aware sustainability nudge with green impact metrics.

    Fetches nearest eco facilities (refill station, recycling bin, EV shuttle),
    computes green impact based on fan actions, and generates a short AI
    encouragement message in the requested language.

    Args:
        gate: Stadium gate or zone name matching a wayfinding_node.
        lang: Target language code (en, es, fr, ar, pt).
        user_refills: Number of water refill actions logged by this fan.
        public_trans_used: Whether the fan arrived via public transport.
        db: Database session dependency.

    Returns:
        Dictionary with nudge text, nearest green stations, impact metrics, and green_score.

    Raises:
        HTTPException: 500 if AI nudge generation fails.
    """
    repo = StadiumRepository(db)
    node = repo.get_wayfinding_node_by_name(gate)

    stations = SustainabilityService.get_refill_and_recycle_stations(gate)
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
    user_prompt = (
        f"The fan is at {gate}. Features info: {node_features}. "
        f"Nearest Refill Station: {stations['nearest_refill']}"
    )

    try:
        nudge = await run_llm_chain(db, system_prompt, user_prompt, lang)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Nudge generation failed: {str(exc)}") from exc

    return {
        "gate": gate,
        "nudge": nudge,
        "nearest_refill": stations["nearest_refill"],
        "nearest_recycle": stations["nearest_recycle"],
        "nearest_ev_shuttle": stations["nearest_ev_shuttle"],
        "green_score": impact["green_score"],
        "plastic_saved_grams": impact["plastic_saved_grams"],
        "co2_reduction_kg": impact["co2_reduction_kg"],
        "eco_rank": impact["eco_rank"],
        "gamification_badges": impact["gamification_badges"],
        "impact": impact,
    }
