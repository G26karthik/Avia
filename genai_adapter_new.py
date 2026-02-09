"""
Avia - GenAI Adapter
Gemini-powered LLM interface. GenAI is a required dependency.
No mock mode, no fallbacks. If Gemini is unavailable, operations fail explicitly.

Usage:
  Set GEMINI_API_KEY env var to your Google AI API key.
"""

import os
import json
import re
from typing import Optional

def _get_gemini_key() -> str:
    """Read GEMINI_API_KEY from environment at call time (not cached at import)."""
    return os.environ.get("GEMINI_API_KEY", "")

GENAI_ERROR_MSG = (
    "AI analysis is temporarily unavailable. "
    "Please try again shortly or contact support."
)


class GenAIUnavailableError(Exception):
    """Raised when GenAI service is unavailable or fails."""
    def __init__(self, reason: str = ""):
        self.reason = reason
        super().__init__(GENAI_ERROR_MSG + (f" ({reason})" if reason else ""))


def check_available() -> bool:
    """Return True if Gemini is configured (API key present)."""
    return bool(_get_gemini_key())


def _call_gemini(prompt: str, system: str = "") -> str:
    from google import genai
    client = genai.Client(api_key=_get_gemini_key())
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt,
    )
    return resp.text.strip()


def call_llm(prompt: str, system: str = "") -> str:
    """Call Gemini. Raises GenAIUnavailableError if unavailable or call fails."""
    if not _get_gemini_key():
        raise GenAIUnavailableError("GEMINI_API_KEY not configured")
    try:
        return _call_gemini(prompt, system)
    except GenAIUnavailableError:
        raise
    except Exception as e:
        raise GenAIUnavailableError(str(e)) from e


# ---------------------------------------------------------------------------
# DOMAIN-SPECIFIC FUNCTIONS
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are Avia, an AI assistant for insurance fraud investigators. "
    "You explain risk findings in plain English. You never use ML jargon, model names, "
    "or mathematical terms. You write as if briefing a human investigator. "
    "Keep responses concise and actionable."
)


def generate_decision_trace(
    claim_data: dict,
    claim_risk: float,
    customer_risk: float,
    pattern_risk: float,
    overall_risk: float,
    risk_level: str,
    top_features: list,
    document_insights: dict = None,
) -> list:
    """Generate a step-by-step decision trace narrative for a claim."""
    doc_section = ""
    if document_insights and document_insights.get("flags"):
        doc_section = f"\nDocument findings: {', '.join(document_insights['flags'])}"

    prompt = f"""Generate a decision trace for an insurance claim investigation. 
This should be a step-by-step narrative (5 steps) showing how the system assessed risk.
Each step should be 1-2 sentences, written for a non-technical investigator.

Claim details:
- Incident type: {claim_data.get('incident_type', 'Not specified')}
- Incident severity: {claim_data.get('incident_severity', 'Not specified')}
- Collision type: {claim_data.get('collision_type', 'Not specified')}
- Total claim amount: ${claim_data.get('total_claim_amount', 'Not specified')}
- Customer tenure: {claim_data.get('customer_tenure_months', claim_data.get('months_as_customer', 'Not available'))}
- Vehicles involved: {claim_data.get('number_of_vehicles_involved', 'Not specified')}
- Bodily injuries: {claim_data.get('bodily_injuries', 'Not specified')}
- Witnesses: {claim_data.get('witnesses', 'Not specified')}
- Police report: {claim_data.get('police_report_available', 'Not specified')}
- Property damage: {claim_data.get('property_damage', 'Not specified')}
- Incident location: {claim_data.get('incident_city', '')}, {claim_data.get('incident_state', '')}
{doc_section}

Risk assessment:
- Claim Risk: {claim_risk:.0f}/100
- Customer Risk: {customer_risk:.0f}/100
- Pattern Risk: {pattern_risk:.0f}/100
- Overall: {overall_risk:.0f}/100 ({risk_level})

Key risk signals: {', '.join(top_features[:5])}

Format your response as a JSON array of 5 strings, each being one step.
Steps should follow this structure:
1. Initial baseline check
2. First concerning signal identified
3. Additional risk factors confirmed
4. Cross-referencing patterns
5. Final risk determination

Return ONLY the JSON array, no other text."""

    response = call_llm(prompt, SYSTEM_PROMPT)
    try:
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    # Try line-based parsing as last resort
    lines = [l.strip() for l in response.split('\n') if l.strip() and len(l.strip()) > 20]
    if lines:
        return lines[:5]
    raise GenAIUnavailableError("Failed to parse decision trace from Gemini response")


def generate_explanation(
    claim_data: dict,
    claim_risk: float,
    customer_risk: float,
    pattern_risk: float,
    risk_level: str,
    top_features: list,
) -> str:
    """Generate a plain-English explanation for an investigator."""
    prompt = f"""Write a brief investigation summary for an insurance claim.
Write as if you're briefing a senior investigator. 3-4 sentences max.
No ML terms, no scores, no math. Just plain judgment.

Claim: {claim_data.get('incident_type', 'Not specified')} incident, ${claim_data.get('total_claim_amount', 'Not specified')} claimed.
Customer tenure: {claim_data.get('customer_tenure_months', claim_data.get('months_as_customer', 'Not available'))}.
Severity: {claim_data.get('incident_severity', 'Not specified')}.
Location: {claim_data.get('incident_city', 'Unknown')}, {claim_data.get('incident_state', 'Unknown')}.
Risk level: {risk_level}.
Key signals: {', '.join(top_features[:4])}.

Write the summary now. Plain text only, no formatting."""

    response = call_llm(prompt, SYSTEM_PROMPT)
    return response


def extract_claim_from_document(ocr_text: str) -> dict:
    """Legacy: Extract claim fields from document text using GenAI. Use extract_claim_multimodal instead."""
    return extract_claim_multimodal_text(ocr_text)


def extract_claim_multimodal_text(ocr_text: str) -> dict:
    """Fallback text-based extraction (not used in primary flow)."""
    prompt = _build_extraction_prompt()
    prompt += f"\n\nDocument text:\n---\n{ocr_text[:4000]}\n---\n\nReturn ONLY the JSON object."
    response = call_llm(prompt, SYSTEM_PROMPT)
    return _parse_extraction_response(response)


def extract_claim_multimodal(file_bytes: bytes, mime_type: str) -> dict:
    """
    PRIMARY extraction: Pass the raw document (image/PDF) directly to Gemini
    for multimodal field extraction. No OCR required.
    
    Returns a dict with extracted fields. Fields that could not be found
    will be set to None.
    """
    if not _get_gemini_key():
        raise GenAIUnavailableError("GEMINI_API_KEY not configured")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=_get_gemini_key())

        prompt = _build_extraction_prompt()
        file_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)

        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[file_part, prompt],
        )
        return _parse_extraction_response(resp.text.strip())

    except GenAIUnavailableError:
        raise
    except Exception as e:
        raise GenAIUnavailableError(str(e)) from e


def _build_extraction_prompt() -> str:
    """Shared prompt for claim field extraction with strict insurance rules."""
    return """You are an expert insurance document analyst. You are reviewing an insurance claim document (could be a form, letter, estimate, photo of a document, police report, repair estimate, or medical bill).

STRICT EXTRACTION RULES - follow these exactly:

1. EXPLICIT EXTRACTION ONLY: Extract a field ONLY if its value is explicitly stated in the document. Never guess, infer, or assume.

2. CUSTOMER TENURE:
   - If BOTH policy_start_date AND incident_date are present in the document, calculate months between them and set "customer_tenure_months" to that number.
   - If either date is missing, set "customer_tenure_months" to null.

3. VEHICLES INVOLVED:
   - If the number of vehicles is explicitly stated, extract the number.
   - If the incident clearly describes a single-vehicle event (e.g. hit a divider, skid, rollover, drove into ditch, single-car accident), set to 1.
   - If ambiguous or not mentioned, set to null.

4. WITNESSES:
   - If witnesses are mentioned with a count, extract that count.
   - If the document explicitly says "no witnesses" or "none", set to 0.
   - If witnesses are not mentioned at all, set to null.

5. POLICY STATE / REGION:
   - Extract ONLY if explicitly present in the document.
   - Otherwise set to null.

6. VEHICLE DETAILS:
   - Extract make, model, year, registration, license plate ONLY if explicitly present.
   - Never guess from context.

7. CLAIM AMOUNT BREAKDOWN:
   - If the document shows a breakdown of the claim (injury, property, vehicle), extract each component.
   - If only total is shown, extract total and leave components as null.

8. INCIDENT LOCATION:
   - Extract city, state, specific location/address if explicitly stated.
   - Extract hour of day if timestamp is present.

9. COLLISION TYPE:
   - For vehicle collisions, extract the type if stated: "Front Collision", "Rear Collision", "Side Collision", or null.

Return ONLY a JSON object with these keys:

POLICY INFORMATION:
- "policy_number": string or null
- "policy_state": string or null (the state where policy is registered)
- "policy_start_date": string in YYYY-MM-DD format or null (policy bind date)
- "policy_deductible": number or null (deductible amount in dollars)
- "policy_annual_premium": number or null (annual premium in dollars)

INCIDENT DETAILS:
- "incident_date": string in YYYY-MM-DD format or null
- "incident_type": string or null (e.g. "Multi-vehicle Collision", "Single Vehicle Collision", "Vehicle Theft", "Parked Car", "Property Damage", "Fire", "Flood")
- "incident_severity": string or null (e.g. "Minor Damage", "Major Damage", "Total Loss", "Trivial Damage")
- "collision_type": string or null (e.g. "Front Collision", "Rear Collision", "Side Collision")
- "incident_state": string or null (state where incident occurred)
- "incident_city": string or null (city where incident occurred)
- "incident_location": string or null (specific address or location description)
- "incident_hour_of_the_day": number (0-23) or null (hour when incident occurred)

CLAIM AMOUNTS:
- "total_claim_amount": number or null (the total dollar amount being claimed)
- "injury_claim": number or null (portion of claim for bodily injuries)
- "property_claim": number or null (portion of claim for property damage)
- "vehicle_claim": number or null (portion of claim for vehicle damage)

PEOPLE & EVIDENCE:
- "customer_tenure_months": number or null (calculated only if both policy_start_date and incident_date are present)
- "bodily_injuries": number or null (number of people injured)
- "witnesses": number or null (0 if explicitly "no witnesses", null if not mentioned)
- "police_report_available": "YES" or "NO" or null
- "property_damage": "YES" or "NO" or null
- "authorities_contacted": string or null (e.g. "Police", "Fire", "Ambulance", "Other")
- "number_of_vehicles_involved": number or null (see rule 3 above)

VEHICLE INFORMATION:
- "vehicle_make": string or null (e.g. "Toyota", "Ford", "Honda")
- "vehicle_model": string or null (e.g. "Camry", "F150", "Civic")
- "vehicle_year": string or null (e.g. "2020")
- "vehicle_registration": string or null (license plate or VIN)
- "insured_vehicle_owner": string or null (name of the vehicle owner)

OTHER:
- "claimant_name": string or null (name of person filing the claim)
- "claimant_contact": string or null (phone or email if present)
- "summary": a 1-sentence factual summary of the claim

Return ONLY the JSON object, no other text."""


def _parse_extraction_response(response: str) -> dict:
    """Parse the GenAI extraction response into a dict. Missing fields are None."""
    SENTINEL_STRINGS = ("", "unknown", "n/a", "none", "not specified",
                        "not available", "not present", "not mentioned",
                        "not present in document")

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            data = json.loads(match.group())
            # Normalize all fields: convert placeholder strings to None
            for key, val in list(data.items()):
                if val is None:
                    continue
                if isinstance(val, str) and val.strip().lower() in SENTINEL_STRINGS:
                    data[key] = None
                # total_claim_amount of 0 means not extracted
                if key == "total_claim_amount" and val == 0:
                    data[key] = None
            return data
    except Exception:
        pass
    # Could not parse - return all None so validation catches it
    return {
        "policy_number": None,
        "incident_type": None,
        "incident_severity": None,
        "total_claim_amount": None,
        "incident_date": None,
    }


def generate_document_insights(ocr_text: str, claim_data: dict) -> dict:
    """Analyze document text for inconsistencies and key values (legacy text-based)."""
    return _generate_document_insights_text(ocr_text, claim_data)


def generate_document_insights_multimodal(file_bytes: bytes, mime_type: str, claim_data: dict) -> dict:
    """Analyze document directly via multimodal Gemini for inconsistencies and key values."""
    if not _get_gemini_key():
        raise GenAIUnavailableError("GEMINI_API_KEY not configured")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=_get_gemini_key())

        prompt = f"""You are reviewing a document submitted with an insurance claim.

Known claim details:
- Claim amount: ${claim_data.get('total_claim_amount', 'Not specified')}
- Incident type: {claim_data.get('incident_type', 'Not specified')}
- Incident date: {claim_data.get('incident_date', 'Not specified')}
- Incident location: {claim_data.get('incident_city', 'Not specified')}, {claim_data.get('incident_state', 'Not specified')}

Analyze this document and return a JSON object with:
1. "summary": A 2-sentence summary of what this document contains.
2. "extracted_values": Key values found (amounts, dates, names, locations) as a dict. Only include values explicitly present.
3. "flags": An array of concerns or inconsistencies (empty array if none). Be precise - only flag real problems.
4. "risk_hints": An array of risk signals from this document (empty array if none).

Return ONLY the JSON object, no other text."""

        file_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)

        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[file_part, prompt],
        )
        response = resp.text.strip()
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise GenAIUnavailableError("Failed to parse document insights from Gemini response")
    except GenAIUnavailableError:
        raise
    except Exception as e:
        raise GenAIUnavailableError(str(e)) from e


def _generate_document_insights_text(ocr_text: str, claim_data: dict) -> dict:
    """Text-based document insights (internal)."""
    prompt = f"""You are reviewing a document submitted with an insurance claim.

Document text (OCR-extracted):
---
{ocr_text[:3000]}
---

Known claim details:
- Claim amount: ${claim_data.get('total_claim_amount', 'Not specified')}
- Incident type: {claim_data.get('incident_type', 'Not specified')}
- Incident date: {claim_data.get('incident_date', 'Not specified')}

Analyze this document and return a JSON object with:
1. "summary": A 2-sentence summary of what this document contains.
2. "extracted_values": Key values found (amounts, dates, names) as a dict.
3. "flags": An array of concerns or inconsistencies (empty array if none).
4. "risk_hints": An array of risk signals from this document (empty array if none).

Return ONLY the JSON object, no other text."""

    response = call_llm(prompt, SYSTEM_PROMPT)
    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    raise GenAIUnavailableError("Failed to parse document insights from Gemini response")
