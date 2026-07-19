import re
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Tuple
from app.database import WayfindingNode, SOPRule, TransitAlert, CrowdSensor

INJECTION_KEYWORDS = [
    "ignore previous", "system prompt", "you are now a", "override instructions",
    "acting as", "forget everything", "developer mode", "jailbreak", "prompt leak"
]

class AISafetyService:
    @staticmethod
    def check_prompt_injection(text: str) -> bool:
        if not text:
            return False
        lower_text = text.lower()
        return any(kw in lower_text for kw in INJECTION_KEYWORDS)

    @staticmethod
    def sanitize_pii(text: str) -> str:
        if not text:
            return ""
        # Redact Phone Numbers
        text = re.sub(r"\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}", "[REDACTED PHONE]", text)
        # Redact Emails
        text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED EMAIL]", text)
        # Redact Credit Cards
        text = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED CARD]", text)
        # Redact Tickets
        text = re.sub(r"\bTKT-\d{4,8}-\b|\bTKT\d{6,10}\b", "[REDACTED TICKET]", text)
        return text

    @staticmethod
    def retrieve_rag_context(db: Session, query: str) -> Dict[str, Any]:
        """
        Retrieves matching nodes, alerts, crowd metrics, and SOPs from the database
        to ground the RAG pipeline.
        """
        query_lower = query.lower()
        context_parts = []
        sources = []

        # Find matching Wayfinding nodes
        nodes = db.query(WayfindingNode).all()
        matched_nodes = []
        for n in nodes:
            if n.name.lower() in query_lower:
                matched_nodes.append(n)
                context_parts.append(
                    f"Waypoint: {n.name} (Zone: {n.zone}, Lat: {n.coordinates_lat}, Lng: {n.coordinates_lng}, "
                    f"Ramp: {n.has_wheelchair_ramp}, Elevator: {n.has_elevator}, "
                    f"Restrooms: {n.restroom_nearby}, First-Aid: {n.first_aid_nearby})"
                )
                sources.append(f"DB.WayfindingNode({n.name})")

        # Find crowd status
        crowds = db.query(CrowdSensor).all()
        for c in crowds:
            if c.zone.lower() in query_lower:
                context_parts.append(f"Crowd Telemetry - Zone {c.zone}: Density is {c.density_percentage}%, Advisory: {c.advisory}")
                sources.append(f"DB.CrowdSensor({c.zone})")

        # Find transit delays
        transits = db.query(TransitAlert).all()
        for t in transits:
            if t.route.lower() in query_lower or "transit" in query_lower or "bus" in query_lower or "metro" in query_lower:
                context_parts.append(f"Transit Service Alert - Route {t.route}: Status is {t.status}, Delay is {t.delay_minutes} minutes")
                sources.append(f"DB.TransitAlert({t.route})")

        # Find SOP rules
        sops = db.query(SOPRule).all()
        for s in sops:
            if s.scenario.lower() in query_lower:
                context_parts.append(f"Official Safety SOP - Scenario '{s.scenario}': Action Plan: {s.action_plan}")
                sources.append(f"DB.SOPRule({s.scenario})")

        return {
            "context": "\n".join(context_parts),
            "sources": list(set(sources))
        }

    @staticmethod
    def verify_output_grounding(db: Session, ai_response: str) -> Tuple[bool, str, List[str]]:
        """
        Scans AI output to verify any referenced gates or locations exist in the DB.
        If a non-existent gate/zone is mentioned, corrects it or marks it invalid.
        """
        valid_nodes = [n.name for n in db.query(WayfindingNode).all()]
        
        # Match capitalized location patterns like "Gate X", "Transit Plaza", etc.
        potential_locations = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", ai_response)
        
        hallucinated_locations = []
        corrected_response = ai_response

        for loc in potential_locations:
            if any(k in loc for k in ["Gate", "Plaza", "Concourse", "Stand"]):
                if loc not in valid_nodes:
                    hallucinated_locations.append(loc)
                    # Find closest match
                    closest = "Gate A"
                    for node_name in valid_nodes:
                        if loc[:4].lower() == node_name[:4].lower():
                            closest = node_name
                            break
                    corrected_response = corrected_response.replace(loc, f"{closest} (Verified Alternative)")

        is_grounded = len(hallucinated_locations) == 0
        return is_grounded, corrected_response, hallucinated_locations

    @classmethod
    async def process_ai_safety(
        cls,
        db: Session,
        query: str,
        ai_response_generator_func
    ) -> Dict[str, Any]:
        """
        Processes query sanitizer, RAG injection, LLM calling, output validation,
        and confidence calculation.
        """
        # 1. Check prompt injection
        if cls.check_prompt_injection(query):
            return {
                "response": "I am sorry, but I cannot process this request due to security protocol violations.",
                "confidence": 0.0,
                "sources": ["System Censor"],
                "fallback_response": "Malicious prompt pattern detected."
            }

        # 2. Sanitize PII
        sanitized_query = cls.sanitize_pii(query)

        # 3. Retrieve database grounding context
        rag_info = cls.retrieve_rag_context(db, sanitized_query)
        context = rag_info["context"]
        sources = rag_info["sources"]

        # If no sources matched and query asks about specific details, confidence drops
        has_specific_queries = any(k in query.lower() for k in ["gate", "route", "alert", "sensor", "emergency", "incident"])
        base_confidence = 0.95 if not has_specific_queries or sources else 0.50

        # 4. Generate AI response (using context)
        raw_response = await ai_response_generator_func(sanitized_query, context)
        if not isinstance(raw_response, str):
            raw_response = str(raw_response)


        # 5. Output Verification
        is_grounded, verified_response, violations = cls.verify_output_grounding(db, raw_response)

        # 6. Calculate Confidence
        confidence = base_confidence
        if not is_grounded:
            confidence -= 0.35
        
        fallback_msg = None
        # Low confidence safe fallback
        if confidence < 0.60:
            verified_response = "I cannot verify this information from trusted stadium data."
            fallback_msg = "Degraded confidence: Output contained unverified gates or coordinates."
            sources = ["System Verifier"]

        return {
            "response": verified_response,
            "confidence": round(confidence, 2),
            "sources": sources if sources else ["General AI Knowledge"],
            "fallback_response": fallback_msg
        }
