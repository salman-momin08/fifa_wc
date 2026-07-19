from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.crowd import CrowdSensorUpdate, CrowdSensorOut
from app.repositories.stadium import StadiumRepository
from app.services.analytics import CrowdAnalyticsService
from app.services.llm import run_llm_chain
from app.api.ws import manager

router = APIRouter()

@router.get("/status")
def get_crowd_status(db: Session = Depends(get_db)):
    repo = StadiumRepository(db)
    sensors = repo.get_crowd_sensors()
    
    result = []
    for s in sensors:
        # Run analytics predictions for each zone
        analytics = CrowdAnalyticsService.predict_density(s.density_percentage)
        result.append({
            "zone": s.zone,
            "density_percentage": s.density_percentage,
            "advisory": s.advisory,
            "predictions": analytics["predictions"],
            "recommendation": analytics["recommendation"],
            "alert_level": analytics["alert_level"]
        })
    return result

@router.post("/update")
async def update_sensor_density(req: CrowdSensorUpdate, db: Session = Depends(get_db)):
    repo = StadiumRepository(db)
    
    # Run GenAI system to create a dynamic plain-language advisory for organizers
    system_prompt = (
        "You are a Crowd Management AI Specialist. Review the incoming density percentage "
        "and generate a brief, actionable advisory notification for tournament coordinators."
    )
    user_prompt = f"Zone: {req.zone}, Current Density: {req.density_percentage}%. Provided alert: {req.advisory or 'None'}"
    
    generated_advisory = await run_llm_chain(db, system_prompt, user_prompt, "en")
    
    # Save/update sensor
    sensor = repo.create_or_update_crowd_sensor(req.zone, req.density_percentage, generated_advisory)
    
    # Predict future congestion
    analytics = CrowdAnalyticsService.predict_density(req.density_percentage)
    
    # Broadcast WebSocket updates
    await manager.broadcast({
        "type": "crowd_update",
        "zone": sensor.zone,
        "density_percentage": sensor.density_percentage,
        "advisory": sensor.advisory,
        "predictions": analytics["predictions"],
        "recommendation": analytics["recommendation"]
    })
    
    return {
        "message": "Sensor updated successfully",
        "zone": sensor.zone,
        "density_percentage": sensor.density_percentage,
        "advisory": sensor.advisory,
        "predictions": analytics["predictions"],
        "recommendation": analytics["recommendation"]
    }
