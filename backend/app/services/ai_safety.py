"""
AI Safety, PII Redaction, Prompt Injection Defense, and RAG Grounding Engine.

Provides sanitization, injection censorship, database RAG context retrieval,
and post-generation coordinate grounding verification.
"""
import re
from typing import Any, Callable, Dict, List, Tuple

from sqlalchemy.orm import Session

from app.database import CrowdSensor, SOPRule, TransitAlert, WayfindingNode

# Keyword blacklist for prompt injection censorship
INJECTION_KEYWORDS: List[str] = [
    "ignore previous",
    "system prompt",
    "you are now a",
    "override instructions",
    "acting as",
    "forget everything",
    "developer mode",
    "jailbreak",
    "prompt leak",
]


class AISafetyService:
    """Service class encapsulating AI safety guardrails and RAG grounding verification."""

    @staticmethod
    def check_prompt_injection(text: str) -> bool:
        """Scan input query text for prompt hijacking and system instruction override patterns.

        Args:
            text: Raw input query string.

        Returns:
            True if potential injection attempt is detected, False otherwise.
        """
        if not text:
            return False
        lower_text = text.lower()
        return any(kw in lower_text for kw in INJECTION_KEYWORDS)

    @staticmethod
    def sanitize_pii(text: str) -> str:
        """Redact sensitive PII (phone numbers, emails, credit cards, ticket serials) using regex.

        Args:
            text: Input query string.

        Returns:
            Sanitized string with PII replaced by redaction placeholders.
        """
        if not text:
            return ""
        text = re.sub(r"\bTKT-\d{4,8}-|\bTKT\d{6,10}\b", "[REDACTED TICKET]", text)
        text = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED CARD]", text)
        text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED EMAIL]", text)
        text = re.sub(
            r"\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
            "[REDACTED PHONE]",
            text,
        )
        return text

    @staticmethod
    def retrieve_rag_context(db: Session, query: str) -> Dict[str, Any]:
        """Retrieve matching waypoints, transit alerts, crowd metrics, and SOPs to ground RAG.

        Args:
            db: Database session dependency.
            query: Sanitized user query string.

        Returns:
            Dictionary with context text string and list of source attribution tags.
        """
        query_lower = query.lower()
        context_parts: List[str] = []
        sources: List[str] = []

        nodes = db.query(WayfindingNode).all()
        for n in nodes:
            if n.name.lower() in query_lower:
                context_parts.append(
                    f"Waypoint: {n.name} (Zone: {n.zone}, Lat: {n.coordinates_lat}, Lng: {n.coordinates_lng}, "
                    f"Ramp: {n.has_wheelchair_ramp}, Elevator: {n.has_elevator}, "
                    f"Restrooms: {n.restroom_nearby}, First-Aid: {n.first_aid_nearby})"
                )
                sources.append(f"DB.WayfindingNode({n.name})")

        crowds = db.query(CrowdSensor).all()
        for c in crowds:
            if c.zone.lower() in query_lower:
                context_parts.append(
                    f"Crowd Telemetry - Zone {c.zone}: Density is {c.density_percentage}%, Advisory: {c.advisory}"
                )
                sources.append(f"DB.CrowdSensor({c.zone})")

        transits = db.query(TransitAlert).all()
        for t in transits:
            if any(k in query_lower for k in [t.route.lower(), "transit", "bus", "metro"]):
                context_parts.append(
                    f"Transit Service Alert - Route {t.route}: Status is {t.status}, Delay is {t.delay_minutes} minutes"
                )
                sources.append(f"DB.TransitAlert({t.route})")

        sops = db.query(SOPRule).all()
        for s in sops:
            if s.scenario.lower() in query_lower:
                context_parts.append(f"Official Safety SOP - Scenario '{s.scenario}': Action Plan: {s.action_plan}")
                sources.append(f"DB.SOPRule({s.scenario})")

        return {"context": "\n".join(context_parts), "sources": list(set(sources))}

    @staticmethod
    def verify_output_grounding(db: Session, ai_response: str) -> Tuple[bool, str, List[str]]:
        """Verify referenced gate locations in AI response against official database nodes.

        Args:
            db: Database session dependency.
            ai_response: Raw generated LLM output string.

        Returns:
            Tuple of (is_grounded_bool, corrected_response_text, hallucinated_locations_list).
        """
        valid_nodes = [n.name for n in db.query(WayfindingNode).all()]
        potential_locations = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", ai_response)

        hallucinated_locations: List[str] = []
        corrected_response = ai_response

        for loc in potential_locations:
            if any(k in loc for k in ["Gate", "Plaza", "Concourse", "Stand"]):
                if loc not in valid_nodes:
                    hallucinated_locations.append(loc)
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
        cls, db: Session, query: str, ai_response_generator_func: Callable[[str, str], Any]
    ) -> Dict[str, Any]:
        """Execute full safety pipeline: injection check, PII scrubbing, RAG context, LLM, grounding.

        Args:
            db: Database session dependency.
            query: Raw user query string.
            ai_response_generator_func: Async callable taking (sanitized_query, context) and returning text.

        Returns:
            Dictionary with response, confidence score, sources list, and optional fallback_response.
        """
        if cls.check_prompt_injection(query):
            return {
                "response": "I am sorry, but I cannot process this request due to security protocol violations.",
                "confidence": 0.0,
                "sources": ["System Censor"],
                "fallback_response": "Malicious prompt pattern detected.",
            }

        sanitized_query = cls.sanitize_pii(query)
        rag_info = cls.retrieve_rag_context(db, sanitized_query)
        context = rag_info["context"]
        sources = rag_info["sources"]

        has_specific_queries = any(
            k in query.lower() for k in ["gate", "route", "alert", "sensor", "emergency", "incident"]
        )
        base_confidence = 0.95 if not has_specific_queries or sources else 0.50

        raw_response = await ai_response_generator_func(sanitized_query, context)
        if not isinstance(raw_response, str):
            raw_response = str(raw_response)

        is_grounded, verified_response, violations = cls.verify_output_grounding(db, raw_response)

        confidence = base_confidence
        if not is_grounded:
            confidence -= 0.35

        fallback_msg = None
        if confidence < 0.60:
            verified_response = "I cannot verify this information from trusted stadium data."
            fallback_msg = "Degraded confidence: Output contained unverified gates or coordinates."
            sources = ["System Verifier"]

        return {
            "response": verified_response,
            "confidence": round(confidence, 2),
            "sources": sources if sources else ["General AI Knowledge"],
            "fallback_response": fallback_msg,
        }
