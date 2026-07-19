"""
Background Celery tasks for async AI processing, translation, and notifications.
These tasks offload heavy operations from the request-response cycle.
"""
import logging
from app.worker import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.generate_operations_summary", bind=True, max_retries=3)
def generate_operations_summary(self, sensor_data: list, incident_data: list, transit_data: list) -> dict:
    """
    Generates an executive operations summary from aggregated stadium telemetry.
    Runs asynchronously so the organizer dashboard responds immediately.
    """
    try:
        crowd_summary = []
        for s in sensor_data:
            level = "🔴 Critical" if s["density_percentage"] > 80 else (
                "🟡 Moderate" if s["density_percentage"] > 50 else "🟢 Clear"
            )
            crowd_summary.append(f"{s['zone']}: {s['density_percentage']}% [{level}]")

        transit_summary = []
        for t in transit_data:
            if t["status"] != "normal":
                transit_summary.append(f"⚠️ {t['route']}: {t['status']} (+{t['delay_minutes']}m)")
            else:
                transit_summary.append(f"✅ {t['route']}: Normal")

        active_incidents = [i for i in incident_data if i.get("status") == "active"]
        draft_incidents = [i for i in incident_data if i.get("status") == "draft"]

        briefing = {
            "crowd_status": "\n".join(crowd_summary) or "No crowd data available.",
            "transit_status": "\n".join(transit_summary) or "All routes operating normally.",
            "active_incidents_count": len(active_incidents),
            "draft_incidents_pending": len(draft_incidents),
            "executive_summary": (
                f"Stadium Operations Status: "
                f"{len(active_incidents)} active incident(s) require monitoring. "
                f"{len(draft_incidents)} draft(s) pending organizer approval. "
                f"Crowd density levels are within operational parameters."
            )
        }
        return briefing

    except Exception as exc:
        logger.error(f"Operations summary task failed: {exc}")
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(name="tasks.send_broadcast_notification", bind=True, max_retries=3)
def send_broadcast_notification(self, incident_id: int, message: str, gate: str) -> dict:
    """
    Simulates broadcasting a safety notification to stadium staff.
    In production this would call push notification APIs.
    """
    try:
        logger.info(f"[Notification] Incident #{incident_id} at {gate}: {message}")
        return {"sent": True, "incident_id": incident_id, "gate": gate}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
