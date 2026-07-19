from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.assistant import AssistantRequest, AssistantOut
from app.repositories.stadium import StadiumRepository
from app.services.ai_safety import AISafetyService
from app.services.route_optimizer import RouteOptimizer
from app.services.llm import run_llm_chain

router = APIRouter()

@router.post("/query", response_model=AssistantOut)
async def query_assistant(req: AssistantRequest, db: Session = Depends(get_db)):
    repo = StadiumRepository(db)
    
    # Check if this is a wayfinding query to optimize the route programmatically
    query_lower = req.query.lower()
    is_route_query = any(k in query_lower for k in ["go from", "route", "wayfinding", "how to get", "directions"])
    
    route_details = None
    if is_route_query:
        # Resolve start and end locations
        start_node = "Transit Plaza"
        end_node = "Gate A"
        accessible = "wheelchair" in query_lower or "ramp" in query_lower or "elevator" in query_lower
        preference = "fastest"
        if "least crowded" in query_lower or "less crowded" in query_lower:
            preference = "least_crowded"
        elif "safest" in query_lower:
            preference = "safest"

        # Check nodes
        nodes = repo.get_wayfinding_nodes()
        for n in nodes:
            if n.name.lower() in query_lower:
                if "from " + n.name.lower() in query_lower:
                    start_node = n.name
                elif "to " + n.name.lower() in query_lower:
                    end_node = n.name

        alerts = repo.get_transit_alerts()
        sensors = repo.get_crowd_sensors()
        
        # Calculate optimal path
        route_details = RouteOptimizer.find_route(
            nodes, alerts, sensors, start_node, end_node, preference, accessible
        )

    # Core LLM prompt call wrapper
    async def ai_generator(sanitized_query: str, context: str) -> str:
        system_prompt = (
            "You are an expert FIFA World Cup 2026 Stadium Operations Assistant. "
            "Provide clear, concise, accessible navigation instructions. "
            "Only reference verified gates and locations. "
            "Use the provided RAG context to ground your answer and prevent hallucinations."
        )
        if route_details and "error" not in route_details:
            route_str = " -> ".join(route_details["route"])
            mode_str = " -> ".join(route_details["modes"])
            context += f"\n[Calculated Optimized Path]: Route: {route_str}, Modes: {mode_str}, ETA: {route_details['eta_minutes']} mins, Accessible: {route_details['accessible']}"
            
        user_prompt = f"User Request: {sanitized_query}\nGrounding Context:\n{context}"
        return await run_llm_chain(db, system_prompt, user_prompt, req.lang)

    try:
        # Run AI processing with Safety Checks & Grounding
        safety_output = AISafetyService.process_ai_safety(db, req.query, lambda q, ctx: run_llm_chain(db, "System Prompt", f"Query: {q}\nContext: {ctx}", req.lang))
        
        # If route was calculated, append structured details to response if not already present
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant processing failed: {str(e)}")
