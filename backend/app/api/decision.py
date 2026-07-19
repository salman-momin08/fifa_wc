"""
Safety Decision Support Copilot Router.

Implements a human-in-the-loop (HITL) safety incident management system.
Field volunteers submit incident reports (DRAFT status); organizers review
AI-generated SOP response plans and approve broadcasts via RBAC-protected endpoints.
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.ws import manager
from app.core.dependencies import RoleChecker
from app.database import Incident, get_db
from app.repositories.stadium import StadiumRepository
from app.schemas.incident import IncidentApproval, IncidentReport
from app.services.llm import run_llm_chain

router = APIRouter()

# Role definitions
is_organizer_or_admin = RoleChecker(["organizer", "admin"])


@router.get("/list")
def list_incidents(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retrieve all logged safety incidents with status and SOP details.

    Args:
        db: Database session dependency.

    Returns:
        List of incident dictionaries.
    """
    repo = StadiumRepository(db)
    incidents = repo.get_incidents()
    return [
        {
            "id": i.id,
            "title": i.title,
            "description": i.description,
            "status": i.status,
            "severity": i.severity,
            "gate": i.gate,
            "suggested_action": i.suggested_action,
            "is_approved": i.is_approved,
            "timestamp": i.timestamp.isoformat(),
        }
        for i in incidents
    ]


@router.post("/report")
async def report_incident(req: IncidentReport, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Log a new safety incident report as a DRAFT and generate an AI SOP action plan.

    Args:
        req: IncidentReport schema with title, description, gate, and severity.
        db: Database session dependency.

    Returns:
        Dictionary containing confirmation message, incident_id, and AI suggested_action.
    """
    repo = StadiumRepository(db)

    # 1. Fetch matching SOP from DB
    sop = repo.get_sop_rule_by_gate_or_keyword(req.gate, req.title)
    sop_info = sop.action_plan if sop else "Standard emergency evacuation and safety protocol."

    # 2. Gather active environment context (Crowd + Transit + Weather)
    sensors = repo.get_crowd_sensors()
    active_crowd_ctx = ""
    for s in sensors:
        if s.zone.lower() in req.gate.lower() or req.gate.lower() in s.zone.lower():
            active_crowd_ctx = f"Current crowd density in this sector: {s.density_percentage}%."
            break

    alerts = repo.get_transit_alerts()
    active_transit_ctx = "No active transport suspensions near this sector."
    for a in alerts:
        if a.status != "normal" and ("shuttle" in a.route.lower() or "metro" in a.route.lower()):
            active_transit_ctx = f"Transit alert: {a.route} status is {a.status} ({a.delay_minutes}m delay)."

    # Mock weather context
    weather_ctx = "Weather: Clear skies, 22°C (72°F)."

    # Historical context: count past incidents at this gate
    incidents_history = repo.get_incidents()
    gate_history_count = sum(1 for i in incidents_history if i.gate == req.gate and i.status == "resolved")
    history_ctx = f"Historical incident frequency at {req.gate}: {gate_history_count} resolved incidents."

    system_prompt = (
        "You are an expert World Cup Safety Coordinator. Review the reported incident "
        "and draft an actionable, step-by-step action plan for stadium staff.\n"
        "You MUST base your suggestions on the official SOP Guideline provided.\n"
        "In your final output, explicitly list:\n"
        "- Recommended Actions (numbered steps)\n"
        "- Safety Confidence Level (High/Medium/Low)\n"
        "- Affected Zones\n"
        "- Escalation Path (who to notify if condition degrades)\n"
        "- Estimated Resolution Time (in minutes)\n"
        "Keep the instructions operational and simple."
    )
    user_prompt = (
        f"Incident: {req.title}. Description: {req.description} at {req.gate}. Severity: {req.severity}.\n"
        f"Official SOP Guideline: {sop_info}\n"
        f"Environmental Context:\n"
        f"- {active_crowd_ctx}\n"
        f"- {active_transit_ctx}\n"
        f"- {weather_ctx}\n"
        f"- {history_ctx}"
    )

    action_plan = await run_llm_chain(db, system_prompt, user_prompt, "en")

    new_incident = Incident(
        title=req.title,
        description=req.description,
        gate=req.gate,
        severity=req.severity,
        status="draft",
        suggested_action=action_plan,
        is_approved=False,
    )
    repo.create_incident(new_incident)

    return {
        "message": "Incident logged as DRAFT. Awaiting Organizer review.",
        "incident_id": new_incident.id,
        "suggested_action": action_plan,
    }


@router.post("/approve")
async def approve_incident(
    req: IncidentApproval,
    db: Session = Depends(get_db),
    current_user=Depends(is_organizer_or_admin),
) -> Dict[str, Any]:
    """Approve a draft safety incident and broadcast its action plan to all connected clients.

    Requires organizer or admin role.

    Args:
        req: IncidentApproval payload with incident_id and optional custom_action.
        db: Database session dependency.
        current_user: Authenticated organizer/admin user model.

    Returns:
        Dictionary with confirmation, incident_id, status, is_approved, and action_plan.

    Raises:
        HTTPException: 404 if incident ID is not found.
    """
    repo = StadiumRepository(db)
    incident = repo.get_incident_by_id(req.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "active"
    incident.is_approved = True
    if req.custom_action:
        incident.suggested_action = req.custom_action

    repo.update_incident(incident)

    # Broadcast incident approval via WebSocket to all connected clients
    await manager.broadcast({
        "type": "incident_approved",
        "incident_id": incident.id,
        "title": incident.title,
        "gate": incident.gate,
        "severity": incident.severity,
        "action_plan": incident.suggested_action,
        "approved_by": current_user.username,
    })

    return {
        "message": "Incident approved and broadcasted to staff and fans.",
        "incident_id": incident.id,
        "status": incident.status,
        "is_approved": incident.is_approved,
        "action_plan": incident.suggested_action,
        "approved_by": current_user.username,
    }
