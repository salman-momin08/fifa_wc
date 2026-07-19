"""
Conversational Multilingual AI Assistant Router.

Handles fan queries with a full safety pipeline: PII redaction, prompt
injection defense, RAG context retrieval, Dijkstra route optimization,
LLM invocation, output grounding verification, and confidence scoring.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.assistant import AssistantRequest, AssistantOut
from app.repositories.stadium import StadiumRepository
from app.services.ai_safety import AISafetyService
from app.services.route_optimizer import RouteOptimizer
from app.services.llm import run_llm_chain

router = APIRouter()

# Route detection keywords
_ROUTE_KEYWORDS = ("go from", "route", "wayfinding", "how to get", "directions", "navigate")
_ACCESSIBLE_KEYWORDS = ("wheelchair", "ramp", "elevator")
_PREFERENCE_MAP = {
    "least crowded": "least_crowded",
    "less crowded": "least_crowded",
    "safest": "safest",
    "fastest": "fastest",
}


@router.post("/query", response_model=AssistantOut)
async def query_assistant(req: AssistantRequest, db: Session = Depends(get_db)) -> AssistantOut:
    """Process a fan query through the full AI safety and RAG grounding pipeline.

    Performs the following steps in sequence:
    1. Detect if query requires Dijkstra pathfinding.
    2. Sanitize PII and check for prompt injection.
    3. Retrieve matching RAG context from DB (nodes, sensors, alerts, SOPs).
    4. Call Google Gemini LLM with grounded system + user prompts.
    5. Verify AI output against DB node records to prevent hallucination.
    6. Return response with confidence score and source attribution.

    Args:
        req: AssistantRequest with query string and target language code.
        db: Database session dependency.

    Returns:
        AssistantOut with response text, confidence, sources, and optional fallback.

    Raises:
        HTTPException: 500 if the AI processing pipeline raises an unhandled error.
    """
    repo = StadiumRepository(db)

    query_lower = req.query.lower()
    is_route_query = any(k in query_lower for k in _ROUTE_KEYWORDS)

    route_details: Optional[dict] = None
    if is_route_query:
        start_node = "Transit Plaza"
        end_node = "Gate A"
        accessible = any(k in query_lower for k in _ACCESSIBLE_KEYWORDS)
        preference = "fastest"
        for keyword, pref in _PREFERENCE_MAP.items():
            if keyword in query_lower:
                preference = pref
                break

        nodes = repo.get_wayfinding_nodes()
        for n in nodes:
            if n.name.lower() in query_lower:
                if f"from {n.name.lower()}" in query_lower:
                    start_node = n.name
                elif f"to {n.name.lower()}" in query_lower:
                    end_node = n.name

        alerts = repo.get_transit_alerts()
        sensors = repo.get_crowd_sensors()
        route_details = RouteOptimizer.find_route(nodes, alerts, sensors, start_node, end_node, preference, accessible)

    async def ai_generator(sanitized_query: str, context: str) -> str:
        """Inner coroutine that builds prompts and invokes the LLM chain."""
        system_prompt = (
            "You are an expert FIFA World Cup 2026 Stadium Operations Assistant. "
            "Provide clear, concise, accessible navigation instructions. "
            "Only reference verified gates and locations. "
            "Use the provided RAG context to ground your answer and prevent hallucinations."
        )
        if route_details and "error" not in route_details:
            route_str = " -> ".join(route_details["route"])
            mode_str = " -> ".join(route_details["modes"])
            context += (
                f"\n[Calculated Optimized Path]: Route: {route_str}, "
                f"Modes: {mode_str}, ETA: {route_details['eta_minutes']} mins, "
                f"Accessible: {route_details['accessible']}"
            )
        user_prompt = f"User Request: {sanitized_query}\nGrounding Context:\n{context}"
        return await run_llm_chain(db, system_prompt, user_prompt, req.lang)

    try:
        safety_output = await AISafetyService.process_ai_safety(db, req.query, ai_generator)

        if route_details and "error" not in route_details and safety_output["confidence"] >= 0.60:
            route_str = " -> ".join(route_details["route"])
            mode_str = " -> ".join(route_details["modes"])
            safety_output["response"] += (
                f"\n\n[Optimized Routing Plan ({route_details['preference']})]:\n"
                f"Path: {route_str}\n"
                f"Transport Modes: {mode_str}\n"
                f"Estimated Duration: {route_details['eta_minutes']} mins."
            )
            safety_output["sources"].append("Local.RouteOptimizer")

        return AssistantOut(**safety_output)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Assistant processing failed: {str(exc)}") from exc
