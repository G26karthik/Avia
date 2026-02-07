"""
Avia â€” Vercel Serverless API
All backend routes handled by a single FastAPI application.
Vercel routes /api/* requests here via vercel.json rewrites.
"""

import os
import sys
import json
import traceback
import warnings
from datetime import datetime
from typing import Optional, List

# Ensure api/ directory is on the import path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# SAFE IMPORTS â€” wrapped to prevent cold-start crashes
# ---------------------------------------------------------------------------
_startup_error = None
try:
    import _db as db
    import _ml_engine as ml_engine
    import _genai_adapter as genai_adapter
    from _genai_adapter import GenAIUnavailableError
except Exception as e:
    _startup_error = f"{type(e).__name__}: {e}"
    print(f"[AVIA] Import error: {_startup_error}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    db = None
    ml_engine = None
    genai_adapter = None
    class GenAIUnavailableError(Exception):
        pass

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
UPLOAD_DIR = "/tmp/avia_uploads" if os.environ.get("VERCEL") else "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Avia â€” Fraud Investigation Platform", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# LAZY DB INIT â€” avoids cold-start crash if DB/CSV has issues
# ---------------------------------------------------------------------------
_db_ready = False


def _ensure_db():
    """Initialize DB on first request (not module level)."""
    global _db_ready
    if _db_ready:
        return
    if _startup_error:
        raise HTTPException(status_code=500, detail=f"Startup error: {_startup_error}")
    if not db:
        raise HTTPException(status_code=500, detail="Database module not loaded")
    try:
        db.init_db()
        _db_ready = True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB init failed: {e}")


# Catch-all: always return JSON, never raw text
@app.exception_handler(Exception)
async def _global_exc(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc), "type": type(exc).__name__})


# ---------------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------------

MAX_CLAIM_DATA_SIZE = 50000
MAX_UPLOAD_SIZE = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateClaimRequest(BaseModel):
    policy_number: str
    claim_data: dict

    @validator("claim_data")
    def validate_claim_data_size(cls, v):
        serialized = json.dumps(v)
        if len(serialized) > MAX_CLAIM_DATA_SIZE:
            raise ValueError(f"claim_data too large (max {MAX_CLAIM_DATA_SIZE} bytes)")
        return v

    @validator("policy_number")
    def validate_policy_number(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("policy_number is required")
        if len(v) > 100:
            raise ValueError("policy_number too long")
        return v.strip()


class DecisionRequest(BaseModel):
    action: str
    notes: Optional[str] = ""

    @validator("notes")
    def validate_notes(cls, v):
        if v and len(v) > 5000:
            raise ValueError("notes too long (max 5000 chars)")
        return v


# ---------------------------------------------------------------------------
# AUTH DEPENDENCY
# ---------------------------------------------------------------------------

def get_current_user(authorization: Optional[str] = Header(None)):
    _ensure_db()
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    token = parts[1]
    session = db.validate_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please log in again.")
    return session


# ---------------------------------------------------------------------------
# AUTH ROUTES
# ---------------------------------------------------------------------------

@app.post("/api/auth/login")
def login(req: LoginRequest):
    _ensure_db()
    user = db.authenticate_by_username(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = db.create_session(user["id"], user["org_id"])
    return {
        "token": token,
        "user_id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
        "org_id": user["org_id"],
        "org_name": user["org_name"],
    }


@app.post("/api/auth/logout")
def logout(current_user: dict = Depends(get_current_user),
          authorization: Optional[str] = Header(None)):
    if authorization:
        token = authorization.split(" ", 1)[1] if " " in authorization else ""
        db.delete_session(token)
    return {"status": "logged out"}


@app.get("/api/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "display_name": current_user["display_name"],
        "role": current_user["role"],
        "org_id": current_user["org_id"],
        "org_name": current_user["org_name"],
    }


# ---------------------------------------------------------------------------
# CLAIMS
# ---------------------------------------------------------------------------

@app.get("/api/claims")
def list_claims(current_user: dict = Depends(get_current_user)):
    org_id = current_user["org_id"]
    claims = db.get_claims(org_id)
    summaries = []
    for c in claims:
        cd = c.get("claim_data", {}) or {}
        summaries.append({
            "id": c["id"],
            "policy_number": c["policy_number"],
            "status": c["status"],
            "source": c.get("source", "dataset"),
            "risk_level": c.get("risk_level"),
            "overall_risk_score": c.get("overall_risk_score"),
            "next_action": _next_action(c.get("risk_level")),
            "incident_type": cd.get("incident_type"),
            "incident_severity": cd.get("incident_severity"),
            "total_claim_amount": cd.get("total_claim_amount"),
            "months_as_customer": cd.get("months_as_customer"),
            "customer_tenure_months": cd.get("customer_tenure_months"),
            "created_at": c.get("created_at"),
            "analyzed_at": c.get("analyzed_at"),
        })
    return {"claims": summaries, "total": len(summaries)}


@app.get("/api/claims/{claim_id}")
def get_claim(claim_id: str, current_user: dict = Depends(get_current_user)):
    org_id = current_user["org_id"]
    claim = db.get_claim(claim_id, org_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    documents = db.get_claim_documents(claim_id)
    decisions = db.get_claim_decisions(claim_id)

    cd = claim.get("claim_data", {}) or {}
    ml_raw = claim.get("ml_raw", {}) or {}

    return {
        "id": claim["id"],
        "policy_number": claim["policy_number"],
        "status": claim["status"],
        "source": claim.get("source", "dataset"),
        "claim_data": cd,
        "risk_level": claim.get("risk_level"),
        "claim_risk_score": claim.get("claim_risk_score"),
        "customer_risk_score": claim.get("customer_risk_score"),
        "pattern_risk_score": claim.get("pattern_risk_score"),
        "overall_risk_score": claim.get("overall_risk_score"),
        "next_action": _next_action(claim.get("risk_level")),
        "ai_explanation": claim.get("ai_explanation"),
        "decision_trace": claim.get("decision_trace"),
        "document_insights": claim.get("document_insights"),
        "top_features": ml_raw.get("top_features", []),
        "documents": [
            {
                "id": d["id"],
                "filename": d["filename"],
                "ai_summary": d.get("ai_summary"),
                "ai_flags": d.get("ai_flags", []),
                "uploaded_at": d.get("uploaded_at"),
            }
            for d in documents
        ],
        "decisions": decisions,
        "created_at": claim.get("created_at"),
        "analyzed_at": claim.get("analyzed_at"),
    }


@app.post("/api/claims")
def create_claim(req: CreateClaimRequest, current_user: dict = Depends(get_current_user)):
    org_id = current_user["org_id"]
    claim_id = db.create_claim(org_id, req.policy_number, req.claim_data)
    return {"claim_id": claim_id, "status": "pending"}


# ---------------------------------------------------------------------------
# UPLOAD â†’ AUTO-CREATE CLAIM
# ---------------------------------------------------------------------------

_EXT_TO_MIME = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}

REQUIRED_EXTRACTION_FIELDS = ["policy_number", "incident_type", "incident_severity", "total_claim_amount"]


@app.post("/api/claims/upload")
async def upload_and_create_claim(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload documents, extract claim data via multimodal GenAI, create claim."""
    org_id = current_user["org_id"]

    if not genai_adapter.check_available():
        raise HTTPException(status_code=503, detail=genai_adapter.GENAI_ERROR_MSG)

    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="At least one file is required")
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per upload")

    file_contents = []
    for file in files:
        safe_filename = os.path.basename(file.filename or "upload").strip()
        if not safe_filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        ext = os.path.splitext(safe_filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}")
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail=f"File '{safe_filename}' too large (max {MAX_UPLOAD_SIZE // (1024*1024)}MB)")
        if len(content) == 0:
            raise HTTPException(status_code=400, detail=f"File '{safe_filename}' is empty")
        file_contents.append((safe_filename, content, ext))

    first_name, first_content, first_ext = file_contents[0]
    mime_type = _EXT_TO_MIME.get(first_ext, "application/octet-stream")

    try:
        extracted = genai_adapter.extract_claim_multimodal(first_content, mime_type)
    except GenAIUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

    missing_fields = []
    for field in REQUIRED_EXTRACTION_FIELDS:
        val = extracted.get(field)
        if val is None:
            missing_fields.append(field)

    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail="Unable to extract required claim details from the document."
        )

    claim_data = {}
    field_map = [
        "policy_number", "incident_type", "incident_severity", "total_claim_amount",
        "incident_date", "policy_start_date", "customer_tenure_months",
        "bodily_injuries", "witnesses", "police_report_available",
        "property_damage", "authorities_contacted", "number_of_vehicles_involved",
        "policy_state", "vehicle_make", "vehicle_model", "vehicle_year",
        "vehicle_registration",
    ]
    for key in field_map:
        val = extracted.get(key)
        if val is not None:
            claim_data[key] = val

    policy_num = claim_data["policy_number"]
    claim_id = db.create_claim(org_id, policy_num, claim_data, source="uploaded")

    claim_dir = os.path.join(UPLOAD_DIR, claim_id)
    os.makedirs(claim_dir, exist_ok=True)
    doc_ids = []

    for safe_filename, content, ext in file_contents:
        file_path = os.path.join(claim_dir, safe_filename)
        with open(file_path, "wb") as f:
            f.write(content)
        doc_id = db.add_document(claim_id, safe_filename, file_path)
        doc_ids.append(doc_id)

        doc_mime = _EXT_TO_MIME.get(ext, "application/octet-stream")
        try:
            insights = genai_adapter.generate_document_insights_multimodal(
                content, doc_mime, claim_data
            )
            db.update_document_analysis(
                doc_id, "",
                insights.get("summary", ""),
                insights.get("flags", [])
            )
        except GenAIUnavailableError:
            db.update_document_analysis(doc_id, "", "", [])

    return {
        "claim_id": claim_id,
        "policy_number": policy_num,
        "extracted": extracted,
        "documents_attached": len(doc_ids),
        "status": "pending",
    }


# ---------------------------------------------------------------------------
# DOCUMENTS
# ---------------------------------------------------------------------------

@app.post("/api/claims/{claim_id}/documents")
async def upload_document(claim_id: str, file: UploadFile = File(...),
                         current_user: dict = Depends(get_current_user)):
    org_id = current_user["org_id"]
    claim = db.get_claim(claim_id, org_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    safe_filename = os.path.basename(file.filename or "upload").strip()
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE // (1024*1024)}MB")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    claim_dir = os.path.join(UPLOAD_DIR, claim_id)
    os.makedirs(claim_dir, exist_ok=True)
    file_path = os.path.join(claim_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    doc_id = db.add_document(claim_id, safe_filename, file_path)

    cd = claim.get("claim_data", {}) or {}
    mime_type = _EXT_TO_MIME.get(ext, "application/octet-stream")
    genai_error = None
    insights = {}
    try:
        insights = genai_adapter.generate_document_insights_multimodal(content, mime_type, cd)
        db.update_document_analysis(
            doc_id, "",
            insights.get("summary", ""),
            insights.get("flags", [])
        )
    except GenAIUnavailableError as e:
        genai_error = str(e)
        db.update_document_analysis(doc_id, "", "", [])

    result = {
        "doc_id": doc_id,
        "filename": safe_filename,
        "summary": insights.get("summary", ""),
        "flags": insights.get("flags", []),
        "risk_hints": insights.get("risk_hints", []),
    }
    if genai_error:
        result["genai_error"] = genai_error
    return result


@app.get("/api/claims/{claim_id}/documents")
def get_documents(claim_id: str, current_user: dict = Depends(get_current_user)):
    org_id = current_user["org_id"]
    claim = db.get_claim(claim_id, org_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    docs = db.get_claim_documents(claim_id)
    return {"documents": [
        {
            "id": d["id"],
            "filename": d["filename"],
            "ai_summary": d.get("ai_summary"),
            "ai_flags": d.get("ai_flags", []),
            "uploaded_at": d.get("uploaded_at"),
        }
        for d in docs
    ]}


# ---------------------------------------------------------------------------
# ANALYZE
# ---------------------------------------------------------------------------

@app.post("/api/claims/{claim_id}/analyze")
def analyze_claim(claim_id: str, current_user: dict = Depends(get_current_user)):
    org_id = current_user["org_id"]
    claim = db.get_claim(claim_id, org_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim_source = claim.get("source", "dataset")
    is_dataset_claim = (claim_source == "dataset")

    docs = db.get_claim_documents(claim_id)
    if not is_dataset_claim and len(docs) == 0:
        raise HTTPException(status_code=400, detail="At least one document must be uploaded before analysis")

    if not genai_adapter.check_available():
        raise HTTPException(status_code=503, detail=genai_adapter.GENAI_ERROR_MSG)

    cd = claim.get("claim_data", {}) or {}

    ml_result = ml_engine.analyze_claim(cd)

    doc_insights = {"summaries": [], "flags": [], "risk_hints": []}
    for doc in docs:
        if doc.get("ai_summary"):
            doc_insights["summaries"].append(doc["ai_summary"])
        if doc.get("ai_flags"):
            flags = doc["ai_flags"] if isinstance(doc["ai_flags"], list) else []
            doc_insights["flags"].extend(flags)

    try:
        decision_trace = genai_adapter.generate_decision_trace(
            claim_data=cd,
            claim_risk=ml_result["claim_risk"],
            customer_risk=ml_result["customer_risk"],
            pattern_risk=ml_result["pattern_risk"],
            overall_risk=ml_result["overall_risk"],
            risk_level=ml_result["risk_level"],
            top_features=ml_result["top_features"],
            document_insights=doc_insights if doc_insights["flags"] else None,
        )
    except GenAIUnavailableError:
        raise HTTPException(status_code=503, detail=genai_adapter.GENAI_ERROR_MSG)

    try:
        explanation = genai_adapter.generate_explanation(
            claim_data=cd,
            claim_risk=ml_result["claim_risk"],
            customer_risk=ml_result["customer_risk"],
            pattern_risk=ml_result["pattern_risk"],
            risk_level=ml_result["risk_level"],
            top_features=ml_result["top_features"],
        )
    except GenAIUnavailableError:
        raise HTTPException(status_code=503, detail=genai_adapter.GENAI_ERROR_MSG)

    analysis = {
        "risk_level": ml_result["risk_level"],
        "claim_risk": ml_result["claim_risk"],
        "customer_risk": ml_result["customer_risk"],
        "pattern_risk": ml_result["pattern_risk"],
        "overall_risk": ml_result["overall_risk"],
        "explanation": explanation,
        "decision_trace": decision_trace,
        "document_insights": doc_insights,
        "ml_raw": {
            **ml_result["ml_raw"],
            "top_features": ml_result["top_features"],
        },
    }
    db.update_claim_analysis(claim_id, analysis)

    return {
        "claim_id": claim_id,
        "risk_level": ml_result["risk_level"],
        "claim_risk": ml_result["claim_risk"],
        "customer_risk": ml_result["customer_risk"],
        "pattern_risk": ml_result["pattern_risk"],
        "overall_risk": ml_result["overall_risk"],
        "next_action": ml_result["next_action"],
        "top_features": ml_result["top_features"],
        "explanation": explanation,
        "decision_trace": decision_trace,
        "document_insights": doc_insights,
    }


# ---------------------------------------------------------------------------
# DECISIONS
# ---------------------------------------------------------------------------

@app.post("/api/claims/{claim_id}/decide")
def decide_claim(claim_id: str, req: DecisionRequest,
                current_user: dict = Depends(get_current_user)):
    org_id = current_user["org_id"]
    user_id = current_user["user_id"]
    claim = db.get_claim(claim_id, org_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if req.action not in ("escalate", "genuine", "defer"):
        raise HTTPException(status_code=400, detail="Action must be: escalate, genuine, or defer")

    dec_id = db.record_decision(claim_id, user_id, req.action, req.notes)
    return {"decision_id": dec_id, "new_status": req.action}


# ---------------------------------------------------------------------------
# INTAKE QUALITY CHECK
# ---------------------------------------------------------------------------

@app.get("/api/claims/{claim_id}/intake-check")
def intake_check(claim_id: str, current_user: dict = Depends(get_current_user)):
    """Check if required fields are present before analysis."""
    _ensure_db()
    org_id = current_user["org_id"]
    claim = db.get_claim(claim_id, org_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    cd = claim.get("claim_data", {}) or {}

    required_fields = {
        "policy_number": "Policy Number",
        "incident_type": "Incident Type",
        "incident_severity": "Incident Severity",
        "total_claim_amount": "Total Claim Amount",
    }

    important_fields = {
        "bodily_injuries": "Bodily Injuries",
        "witnesses": "Witnesses",
        "police_report_available": "Police Report",
        "property_damage": "Property Damage",
        "authorities_contacted": "Authorities Contacted",
        "number_of_vehicles_involved": "Vehicles Involved",
    }

    def _is_empty(val):
        if val is None or val == '':
            return True
        if isinstance(val, str) and val.lower().strip() in ['unknown', 'n/a', 'none', '\u2014', '-', 'not available', 'not mentioned']:
            return True
        return False

    missing_required = []
    present_required = []
    for key, label in required_fields.items():
        val = cd.get(key) or claim.get(key)
        if _is_empty(val):
            missing_required.append({"field": key, "label": label})
        else:
            present_required.append({"field": key, "label": label, "value": val})

    missing_important = []
    present_important = []
    for key, label in important_fields.items():
        val = cd.get(key)
        if _is_empty(val):
            missing_important.append({"field": key, "label": label})
        else:
            present_important.append({"field": key, "label": label, "value": val})

    inconsistencies = []
    amount = cd.get("total_claim_amount")
    if amount is not None:
        try:
            amt = float(str(amount).replace(',', '').replace('$', ''))
            if amt <= 0:
                inconsistencies.append("Claim amount is zero or negative")
            if amt > 1000000:
                inconsistencies.append("Unusually high claim amount (>$1M)")
        except (ValueError, TypeError):
            pass

    docs = db.get_claim_documents(claim_id)
    has_documents = len(docs) > 0
    is_dataset = claim.get("source", "dataset") == "dataset"

    if not is_dataset and not has_documents:
        inconsistencies.append("No supporting documents attached")

    if missing_required:
        status = "INCOMPLETE"
        message = f"Missing {len(missing_required)} required field(s). Claim cannot be analyzed until these are provided."
    elif missing_important:
        status = "NEEDS_MORE_INFO"
        message = f"All required fields present. {len(missing_important)} optional field(s) missing \u2014 analysis may be less accurate."
    else:
        status = "READY"
        message = "All fields present. Claim is ready for analysis."

    if inconsistencies and status == "READY":
        status = "NEEDS_MORE_INFO"
        message = "All fields present but some inconsistencies detected. Review before analysis."

    return {
        "claim_id": claim_id,
        "status": status,
        "message": message,
        "required": {"present": present_required, "missing": missing_required},
        "important": {"present": present_important, "missing": missing_important},
        "inconsistencies": inconsistencies,
        "has_documents": has_documents,
        "is_dataset_claim": is_dataset,
    }


# ---------------------------------------------------------------------------
# ESCALATION PACKAGE
# ---------------------------------------------------------------------------

@app.get("/api/claims/{claim_id}/escalation-package")
def escalation_package(claim_id: str, current_user: dict = Depends(get_current_user)):
    """Generate a structured escalation package for SIU."""
    _ensure_db()
    org_id = current_user["org_id"]
    claim = db.get_claim(claim_id, org_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    cd = claim.get("claim_data", {}) or {}
    decisions = db.get_claim_decisions(claim_id)
    docs = db.get_claim_documents(claim_id)
    ml_raw = claim.get("ml_raw", {}) or {}

    summary = {
        "claim_id": claim["id"],
        "policy_number": claim["policy_number"],
        "status": claim["status"],
        "source": claim.get("source", "dataset"),
        "risk_level": claim.get("risk_level", "Not assessed"),
        "overall_risk_score": claim.get("overall_risk_score"),
        "incident_type": cd.get("incident_type", "Not specified"),
        "incident_severity": cd.get("incident_severity", "Not specified"),
        "total_claim_amount": cd.get("total_claim_amount", "Not specified"),
        "created_at": claim.get("created_at"),
        "analyzed_at": claim.get("analyzed_at"),
    }

    risk_factors = {
        "claim_risk_score": claim.get("claim_risk_score"),
        "customer_risk_score": claim.get("customer_risk_score"),
        "pattern_risk_score": claim.get("pattern_risk_score"),
        "top_features": ml_raw.get("top_features", []),
        "ai_explanation": claim.get("ai_explanation"),
    }

    evidence = {
        "decision_trace": claim.get("decision_trace", []),
        "document_insights": claim.get("document_insights", {}),
        "documents": [
            {
                "filename": d.get("filename"),
                "ai_summary": d.get("ai_summary"),
                "ai_flags": d.get("ai_flags", []),
            }
            for d in docs
        ],
    }

    notes = [
        {
            "action": d.get("action"),
            "notes": d.get("notes"),
            "by": d.get("investigator_name") or d.get("display_name") or d.get("user_id"),
            "at": d.get("decided_at"),
        }
        for d in decisions
    ]

    lines = []
    lines.append("=" * 60)
    lines.append("AVIA â€” ESCALATION PACKAGE")
    lines.append("=" * 60)
    lines.append("")
    lines.append("CLAIM SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Claim ID:        {summary['claim_id']}")
    lines.append(f"Policy Number:   {summary['policy_number']}")
    lines.append(f"Status:          {summary['status']}")
    lines.append(f"Risk Level:      {summary['risk_level']}")
    lines.append(f"Risk Score:      {summary.get('overall_risk_score', 'N/A')}")
    lines.append(f"Incident Type:   {summary['incident_type']}")
    lines.append(f"Severity:        {summary['incident_severity']}")
    lines.append(f"Claim Amount:    {summary['total_claim_amount']}")
    lines.append(f"Created:         {summary.get('created_at', 'N/A')}")
    lines.append(f"Analyzed:        {summary.get('analyzed_at', 'N/A')}")
    lines.append("")
    lines.append("KEY RISK FACTORS")
    lines.append("-" * 40)
    lines.append(f"Claim Risk:      {risk_factors.get('claim_risk_score', 'N/A')}")
    lines.append(f"Customer Risk:   {risk_factors.get('customer_risk_score', 'N/A')}")
    lines.append(f"Pattern Risk:    {risk_factors.get('pattern_risk_score', 'N/A')}")
    if risk_factors.get("top_features"):
        lines.append(f"Indicators:      {', '.join(risk_factors['top_features'])}")
    if risk_factors.get("ai_explanation"):
        lines.append(f"")
        lines.append(f"AI Assessment:")
        lines.append(risk_factors["ai_explanation"])
    lines.append("")
    lines.append("EXTRACTED EVIDENCE")
    lines.append("-" * 40)
    for i, step in enumerate(evidence.get("decision_trace", []), 1):
        text = step if isinstance(step, str) else step.get("detail", step.get("title", str(step)))
        lines.append(f"  {i}. {text}")
    if evidence.get("documents"):
        lines.append(f"")
        lines.append(f"Documents ({len(evidence['documents'])}):")
        for doc in evidence["documents"]:
            lines.append(f"  - {doc['filename']}")
            if doc.get("ai_summary"):
                lines.append(f"    Summary: {doc['ai_summary']}")
            for flag in doc.get("ai_flags", []):
                lines.append(f"    Flag: {flag}")
    lines.append("")
    lines.append("INVESTIGATOR NOTES")
    lines.append("-" * 40)
    if notes:
        for n in notes:
            lines.append(f"  [{(n.get('action') or '').upper()}] by {n.get('by', 'Unknown')} at {n.get('at', 'Unknown')}")
            if n.get("notes"):
                lines.append(f"    {n['notes']}")
    else:
        lines.append("  No investigator notes recorded.")
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"Generated: {datetime.utcnow().isoformat()}Z")
    lines.append("Avia - Fraud Investigation Platform")

    plain_text = "\n".join(lines)

    return {
        "claim_id": claim_id,
        "summary": summary,
        "risk_factors": risk_factors,
        "evidence": evidence,
        "investigator_notes": notes,
        "plain_text": plain_text,
    }


# ---------------------------------------------------------------------------
# HEALTH
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    """Diagnostic endpoint â€” works even if DB or imports failed."""
    info = {
        "status": "ok" if not _startup_error else "degraded",
        "startup_error": _startup_error,
        "db_ready": _db_ready,
        "python": sys.version,
        "vercel": bool(os.environ.get("VERCEL")),
        "genai_provider": "gemini",
        "genai_model": "gemini-2.5-flash",
    }
    try:
        if genai_adapter:
            info["genai_ready"] = genai_adapter.check_available()
        else:
            info["genai_ready"] = False
    except Exception as e:
        info["genai_ready"] = False
        info["genai_error"] = str(e)
    try:
        if ml_engine:
            info["ml_models_loaded"] = ml_engine._load_models()
        else:
            info["ml_models_loaded"] = False
    except Exception as e:
        info["ml_models_loaded"] = False
    return info


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _next_action(risk_level: str) -> str:
    if risk_level == "High":
        return "Escalation Recommended"
    elif risk_level == "Medium":
        return "Further Review Needed"
    return "Routine â€” Proceed to Close"
