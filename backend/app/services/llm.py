"""
Google Gemini LLM Integration & Deterministic Fallback Engine.

Manages grounded Gemini REST API calls, PII scrubbing, injection censorship,
and multi-language deterministic SOP fallbacks (English, Spanish, French, Arabic, Portuguese).
"""
import os
import re
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.database import CrowdSensor, SOPRule, TransitAlert, WayfindingNode

# Regex patterns for PII Redaction
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE = re.compile(r"\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}")
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
TICKET_RE = re.compile(r"\bTKT-\d{4,8}-\b|\bTKT\d{6,10}\b")

# Bad tokens suggesting prompt injection
INJECTION_KEYWORDS = [
    "ignore previous", "system prompt", "you are now a", "override instructions",
    "acting as", "forget everything", "developer mode"
]

def sanitize_user_input(text: str) -> str:
    """
    Redact PII from the input query.
    """
    if not text:
        return ""
    
    # 1. Check for prompt injection
    lower_text = text.lower()
    for kw in INJECTION_KEYWORDS:
        if kw in lower_text:
            # Neutralize injection by clearing or flagging
            text = "[System Censor: Potential Prompt Injection Attempt Blocked]"
            break
            
    # 2. Redact PII
    text = EMAIL_RE.sub("[REDACTED EMAIL]", text)
    text = PHONE_RE.sub("[REDACTED PHONE]", text)
    text = CREDIT_CARD_RE.sub("[REDACTED CARD]", text)
    text = TICKET_RE.sub("[REDACTED TICKET]", text)
    
    return text

def verify_and_correct_locations(db: Session, text: str) -> str:
    """
    Scans the generated text for mentions of gates or landmarks.
    If a gate/location is mentioned, verifies it exists in the database.
    If it does not exist, marks it or replaces it with a verified one.
    """
    # Fetch all valid node names from DB
    valid_nodes = [node.name for node in db.query(WayfindingNode).all()]
    
    # Find patterns like "Gate X" or "Transit Plaza"
    # Let's extract any potential locations by matching capital letter words/phrases
    potential_locations = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
    
    for loc in potential_locations:
        # Check if it sounds like a gate or station but isn't in valid_nodes
        if ("Gate" in loc or "Plaza" in loc or "Concourse" in loc or "Stand" in loc):
            if loc not in valid_nodes:
                # Find closest verified gate (e.g., matching first characters or default Gate A)
                closest = "Gate A (Verified)"
                for node_name in valid_nodes:
                    if loc[:4].lower() == node_name[:4].lower():
                        closest = node_name
                        break
                text = text.replace(loc, f"{closest} (Alternative for non-existent {loc})")
                
    return text

def translate_fallback(text: str, lang: str) -> str:
    """
    Simple static translation lookup for multilingual support under degraded offline conditions.
    """
    translations = {
        "es": {
            "High Density": "Densidad Alta",
            "Slow entry flow, recommend redirection.": "Flujo de entrada lento, se recomienda redireccionamiento.",
            "Moderate Density": "Densidad Moderada",
            "Flowing smoothly.": "Fluyendo sin problemas.",
            "Low Density": "Densidad Baja",
            "Entry clear.": "Entrada despejada.",
            "Verified": "Verificado",
            "Emergency Plan Activated": "Plan de Emergencia Activado",
            "Transit delay": "Retraso de tránsito",
            "delay": "retraso",
            "minutes": "minutos",
            "is currently normal": "está normal actualmente",
            "wheelchair accessible": "accesible para sillas de ruedas",
            "restroom nearby": "baño cercano",
            "first aid nearby": "primeros auxilios cercanos",
            "To go from": "Para ir de",
            "to": "a",
            "proceed to": "proceda a"
        },
        "fr": {
            "High Density": "Densité Élevée",
            "Slow entry flow, recommend redirection.": "Flux d'entrée lent, redirection recommandée.",
            "Moderate Density": "Densité Modérée",
            "Flowing smoothly.": "Fluide.",
            "Low Density": "Densité Faible",
            "Entry clear.": "Entrée libre.",
            "Verified": "Vérifié",
            "Emergency Plan Activated": "Plan d'Urgence Activé",
            "Transit delay": "Retard de transport",
            "delay": "retard",
            "minutes": "minutes",
            "is currently normal": "est actuellement normal",
            "wheelchair accessible": "accessible aux personnes en fauteuil roulant",
            "restroom nearby": "toilettes à proximité",
            "first aid nearby": "premiers secours à proximité",
            "To go from": "Pour aller de",
            "to": "à",
            "proceed to": "procédez vers"
        },
        "ar": {
            "High Density": "كثافة عالية",
            "Slow entry flow, recommend redirection.": "دخول بطيء، ننصح بتغيير المسار.",
            "Moderate Density": "كثافة متوسطة",
            "Flowing smoothly.": "تدفق سلس.",
            "Low Density": "كثافة منخفضة",
            "Entry clear.": "المدخل خالٍ.",
            "Verified": "تم التحقق",
            "Emergency Plan Activated": "تم تفعيل خطة الطوارئ",
            "Transit delay": "تأخر النقل",
            "delay": "تأخير",
            "minutes": "دقائق",
            "is currently normal": "يعمل بشكل طبيعي",
            "wheelchair accessible": "متاح للكراسي المتحركة",
            "restroom nearby": "دورة مياه قريبة",
            "first aid nearby": "الإسعافات الأولية قريبة",
            "To go from": "للذهاب من",
            "to": "إلى",
            "proceed to": "اتجه نحو"
        },
        "pt": {
            "High Density": "Densidade Alta",
            "Slow entry flow, recommend redirection.": "Fluxo de entrada lento, recomenda-se redirecionamento.",
            "Moderate Density": "Densidade Moderada",
            "Flowing smoothly.": "Fluindo suavemente.",
            "Low Density": "Densidade Baixa",
            "Entry clear.": "Entrada livre.",
            "Verified": "Verificado",
            "Emergency Plan Activated": "Plano de Emergência Ativado",
            "Transit delay": "Atraso no trânsito",
            "delay": "atraso",
            "minutes": "minutos",
            "is currently normal": "está normal atualmente",
            "wheelchair accessible": "acessível para cadeiras de rodas",
            "restroom nearby": "banheiro próximo",
            "first aid nearby": "primeiros socorros próximos",
            "To go from": "Para ir de",
            "to": "para",
            "proceed to": "siga para"
        }
    }
    
    # Apply replacements if language is supported
    target = lang.lower()
    if target in translations:
        dict_trans = translations[target]
        translated_text = text
        for en_word, trans_word in dict_trans.items():
            translated_text = re.sub(r'\b' + re.escape(en_word) + r'\b', trans_word, translated_text, flags=re.IGNORECASE)
        return translated_text
        
    return text

async def run_llm_chain(db: Session, system_prompt: str, user_prompt: str, lang: str = "en") -> str:
    """
    Main LLM prompt runner.
    If GEMINI_API_KEY is available, executes via Gemini API.
    Otherwise, falls back to a rules-based deterministic generation based on SQL data.
    """
    sanitized_user = sanitize_user_input(user_prompt)
    
    # Check if there is an injection blockade
    if "[System Censor:" in sanitized_user:
        return "I am sorry, but I cannot process this request due to security protocol violations."

    gemini_key = os.environ.get("GEMINI_API_KEY")
    result_text = ""
    
    if gemini_key:
        try:
            # Safe call structure with XML constraints
            xml_user_prompt = f"<system_context>{system_prompt}</system_context>\n<user_query>{sanitized_user}</user_query>"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": xml_user_prompt}]}]
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    result_text = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            # Fallback to local rule evaluation on LLM failure
            print(f"LLM call failed: {e}. Degrading to offline static rules.")
            result_text = ""
            
    # Local fallback engine (offline mode)
    if not result_text:
        # Match intents in user_prompt
        query = sanitized_user.lower()
        if "go from" in query or "wayfinding" in query or "route" in query or "how to get" in query:
            # Wayfinding Intent
            start_node = "Transit Plaza"
            end_node = "Gate A"
            accessible = "wheelchair" in query or "ramp" in query or "elevator" in query
            
            # Try to identify start/end in DB
            nodes = db.query(WayfindingNode).all()
            for n in nodes:
                if n.name.lower() in query:
                    if "from " + n.name.lower() in query:
                        start_node = n.name
                    elif "to " + n.name.lower() in query:
                        end_node = n.name
            
            start = db.query(WayfindingNode).filter(WayfindingNode.name == start_node).first()
            end = db.query(WayfindingNode).filter(WayfindingNode.name == end_node).first()
            
            if start and end:
                features = []
                if accessible:
                    features.append("wheelchair accessible path")
                if end.has_wheelchair_ramp:
                    features.append("wheelchair ramp active")
                if end.restroom_nearby:
                    features.append("restroom nearby")
                if end.first_aid_nearby:
                    features.append("first aid nearby")
                
                feat_str = f" [{', '.join(features)}]" if features else ""
                result_text = (
                    f"To go from {start.name} (Lat: {start.coordinates_lat}, Lng: {start.coordinates_lng}) "
                    f"to {end.name} (Lat: {end.coordinates_lat}, Lng: {end.coordinates_lng}), "
                    f"proceed to Concourse West, then follow signs to the outer gates.{feat_str}"
                )
            else:
                result_text = "Standard waypoint route: Proceed along the designated concourse ring to your target gate."
                
        elif "crowd" in query or "density" in query or "gate flow" in query:
            # Crowd Intent
            sensors = db.query(CrowdSensor).all()
            reports = []
            for s in sensors:
                reports.append(f"{s.zone}: {s.density_percentage}% density. {s.advisory}")
            result_text = "Crowd Density Advisories:\n" + "\n".join(reports)
            
        elif "transit" in query or "bus" in query or "metro" in query or "parking" in query:
            # Transit Intent
            alerts = db.query(TransitAlert).all()
            reports = []
            for a in alerts:
                if a.status != "normal":
                    reports.append(f"Transit delay: {a.route} is {a.status} with a delay of {a.delay_minutes} minutes.")
                else:
                    reports.append(f"{a.route} is currently normal.")
            result_text = "Transit Network Status:\n" + "\n".join(reports)
            
        elif "sustainability" in query or "recycle" in query or "waste" in query:
            # Sustainability Intent
            result_text = (
                "Sustainability Nudge: Help us keep the stadium green! Refill your water bottle at "
                "Concourse West refill station and throw recyclables in the Green Bin near Gate B."
            )
            
        elif "incident" in query or "emergency" in query or "sop" in query:
            # Emergency SOP Incident Intent
            sops = db.query(SOPRule).all()
            matched = False
            for s in sops:
                if s.scenario.lower() in query:
                    result_text = f"Emergency Plan Activated for [{s.scenario}]:\n{s.action_plan}"
                    matched = True
                    break
            if not matched:
                result_text = "Standard Operational Incident Protocol: Secure the zone, guide spectators away, and notify volunteer services."
                
        else:
            result_text = (
                "Welcome to the FIFA World Cup 2026 Stadium Operations Assistant. I can assist with "
                "accessible wayfinding, crowd flow reports, live transit delays, sustainability tips, and SOP instructions."
            )
            
    # Verify and correct any coordinates/gates in output to avoid hallucinations
    result_text = verify_and_correct_locations(db, result_text)
    
    # Translate text if necessary
    result_text = translate_fallback(result_text, lang)
    
    return result_text
