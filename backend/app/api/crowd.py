"""
Crowd Intelligence Router.

Exposes real-time crowd density sensor status and density update endpoints.
Integrates the CrowdAnalyticsService for 15/30/60-minute predictive forecasting
and broadcasts zone updates to connected clients via WebSockets.
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.crowd import CrowdSensorUpdate
from app.repositories.stadium import StadiumRepository
from app.services.analytics import CrowdAnalyticsService
from app.services.llm import run_llm_chain
from app.api.ws import manager

router = APIRouter()


@router.get("/status")
def get_crowd_status(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retrieve current crowd density readings with 15/30/60-minute predictive forecasts.

    Queries all crowd sensor zones and enriches each with density predictions,
    an explainable recommendation, and an alert level classification.

    Args:
        db: Database session dependency.

    Returns:
        List of zone telemetry dictionaries with zone, density_percentage, advisory,
        predictions (in_15_mins, in_30_mins, in_60_mins), recommendation, and alert_level.
    """
    repo = StadiumRepository(db)
    sensors = repo.get_crowd_sensors()

    result = []
    for s in sensors:
        analytics = CrowdAnalyticsService.predict_density(s.density_percentage)
        result.append({
            "zone": s.zone,
            "density_percentage": s.density_percentage,
            "advisory": s.advisory,
            "predictions": analytics["predictions"],
            "recommendation": analytics["recommendation"],
            "alert_level": analytics["alert_level"],
        })
    return result


@router.post("/update")
async def update_sensor_density(req: CrowdSensorUpdate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Update crowd sensor density for a zone and broadcast an AI-generated advisory.

    Generates a dynamic advisory via Google Gemini, persists the sensor reading,
    computes predictive forecasts, and pushes a WebSocket update to all clients.

    Args:
        req: Sensor update payload (zone, density_percentage, optional advisory).
        db: Database session dependency.

    Returns:
        Confirmation dict with zone, density_percentage, advisory, and predictions.

    Raises:
        HTTPException: 500 if sensor update or AI advisory generation fails.
    """
    repo = StadiumRepository(db)

    system_prompt = (
        "You are a Crowd Management AI Specialist. Review the incoming density percentage "
        "and generate a brief, actionable advisory notification for tournament coordinators."
    )
    user_prompt = f"Zone: {req.zone}, Current Density: {req.density_percentage}%. Provided alert: {req.advisory or 'None'}"

    try:
        generated_advisory = await run_llm_chain(db, system_prompt, user_prompt, "en")
        sensor = repo.create_or_update_crowd_sensor(req.zone, req.density_percentage, generated_advisory)
        analytics = CrowdAnalyticsService.predict_density(req.density_percentage)

        await manager.broadcast({
            "type": "crowd_update",
            "zone": sensor.zone,
            "density_percentage": sensor.density_percentage,
            "advisory": sensor.advisory,
            "predictions": analytics["predictions"],
            "recommendation": analytics["recommendation"],
        })

        return {
            "message": "Sensor updated successfully",
            "zone": sensor.zone,
            "density_percentage": sensor.density_percentage,
            "advisory": sensor.advisory,
            "predictions": analytics["predictions"],
            "recommendation": analytics["recommendation"],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sensor update failed: {str(exc)}") from exc
