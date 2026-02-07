"""
Avia — Database Layer (Vercel Serverless)
Uses SQLite in /tmp/ for Vercel (ephemeral), or local avia.db for development.
Manages organizations, users, claims, documents, and investigator decisions.
Seeds 5 demo organizations with distinct claims on cold start.
"""

import sqlite3
import os
import json
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# On Vercel, use /tmp/ (only writable directory). Locally, use project dir.
IS_VERCEL = bool(os.environ.get("VERCEL"))
DB_PATH = "/tmp/avia.db" if IS_VERCEL else os.environ.get("AVIA_DB_PATH", "avia.db")

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
CSV_PATH = os.path.join(_PROJECT_ROOT, "insurance_fraud.csv")

# ---------------------------------------------------------------------------
# DEMO ORGANIZATIONS & USERS
# ---------------------------------------------------------------------------
DEMO_ORGS = [
    {
        "id": "org-apex",
        "name": "Apex Insurance Co.",
        "users": [
            {"id": "user-apex-01", "username": "jsmith", "display_name": "John Smith", "role": "investigator"},
            {"id": "user-apex-02", "username": "mlee", "display_name": "Maria Lee", "role": "senior_investigator"},
        ],
        "claim_slice": (0, 15),
    },
    {
        "id": "org-nova",
        "name": "Nova Assurance",
        "users": [
            {"id": "user-nova-01", "username": "aturner", "display_name": "Alex Turner", "role": "investigator"},
        ],
        "claim_slice": (15, 25),
    },
    {
        "id": "org-zenith",
        "name": "Zenith General Insurance",
        "users": [
            {"id": "user-zenith-01", "username": "pshah", "display_name": "Priya Shah", "role": "investigator"},
        ],
        "claim_slice": (25, 35),
    },
    {
        "id": "org-horizon",
        "name": "Horizon Mutual",
        "users": [
            {"id": "user-horizon-01", "username": "dchen", "display_name": "David Chen", "role": "investigator"},
        ],
        "claim_slice": (35, 45),
    },
    {
        "id": "org-reliance",
        "name": "Reliance Shield",
        "users": [
            {"id": "user-reliance-01", "username": "rkumar", "display_name": "Raj Kumar", "role": "investigator"},
        ],
        "claim_slice": (45, 50),
    },
]

DEFAULT_PASSWORD = "avia2026"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


_initialized = False


def init_db():
    """Create tables, seed orgs/users/claims. Idempotent."""
    global _initialized
    if _initialized and os.path.exists(DB_PATH):
        return
    _initialized = True

    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            role TEXT DEFAULT 'investigator',
            password_hash TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        );

        CREATE TABLE IF NOT EXISTS claims (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            policy_number TEXT,
            claim_data JSON,
            source TEXT DEFAULT 'uploaded',
            status TEXT DEFAULT 'pending',
            risk_level TEXT,
            claim_risk_score REAL,
            customer_risk_score REAL,
            pattern_risk_score REAL,
            overall_risk_score REAL,
            ai_explanation TEXT,
            decision_trace JSON,
            document_insights JSON,
            ml_raw JSON,
            created_at TEXT DEFAULT (datetime('now')),
            analyzed_at TEXT,
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        );

        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            claim_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            ocr_text TEXT,
            ai_summary TEXT,
            ai_flags JSON,
            uploaded_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (claim_id) REFERENCES claims(id)
        );

        CREATE TABLE IF NOT EXISTS decisions (
            id TEXT PRIMARY KEY,
            claim_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            notes TEXT,
            decided_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (claim_id) REFERENCES claims(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            org_id TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        );
    """)

    # Seed orgs + users if empty
    if conn.execute("SELECT COUNT(*) FROM organizations").fetchone()[0] == 0:
        pw_hash = _hash_password(DEFAULT_PASSWORD)
        for org in DEMO_ORGS:
            conn.execute("INSERT INTO organizations (id, name) VALUES (?, ?)",
                         (org["id"], org["name"]))
            for user in org["users"]:
                conn.execute(
                    "INSERT INTO users (id, org_id, username, display_name, role, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (user["id"], org["id"], user["username"], user["display_name"], user["role"], pw_hash))
        conn.commit()

        # Seed claims from CSV for each org
        _seed_all_org_claims(conn)

    conn.close()


def _seed_all_org_claims(conn):
    """Seed claims from CSV, distributing across the 5 demo organizations."""
    if not os.path.exists(CSV_PATH):
        return

    import csv as _csv
    import random
    import math

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = _csv.DictReader(f)
        all_rows = list(reader)

    for org in DEMO_ORGS:
        start, end = org["claim_slice"]
        org_rows = all_rows[start:end]
        claim_ids = []

        for row in org_rows:
            claim_data = dict(row)
            policy_num = str(claim_data.get("policy_number", f"POL-{start}"))
            claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
            conn.execute(
                "INSERT INTO claims (id, org_id, policy_number, claim_data, source, status) VALUES (?, ?, ?, ?, ?, ?)",
                (claim_id, org["id"], policy_num, json.dumps(claim_data, default=str), "dataset", "pending"))
            claim_ids.append((claim_id, claim_data))

        conn.commit()

        # Pre-analyze ~60% of each org's claims
        rng = random.Random(hash(org["id"]))
        analyze_count = max(1, int(len(claim_ids) * 0.6))
        to_analyze = rng.sample(claim_ids, min(analyze_count, len(claim_ids)))

        primary_user = org["users"][0]["id"]
        for claim_id, claim_data in to_analyze:
            _seed_fake_analysis(conn, claim_id, claim_data, rng, primary_user)

        conn.commit()


def _seed_fake_analysis(conn, claim_id: str, claim_data: dict, rng, user_id: str):
    """Generate realistic pre-analyzed data for a seeded claim."""
    amount = float(claim_data.get("total_claim_amount", 0) or 0)
    tenure = float(claim_data.get("months_as_customer", 50) or 50)
    severity = str(claim_data.get("incident_severity", "")).lower()
    incident_type = str(claim_data.get("incident_type", "")).replace("_", " ")
    police = str(claim_data.get("police_report_available", "")).lower()
    fraud_reported = str(claim_data.get("fraud_reported", "")).upper()

    claim_risk = min(100, max(5, amount / 800 + rng.uniform(-10, 15)))
    if "total" in severity:
        claim_risk = min(100, claim_risk + rng.uniform(15, 30))
    elif "major" in severity:
        claim_risk = min(100, claim_risk + rng.uniform(5, 15))

    customer_risk = min(100, max(5, 80 - tenure * 0.5 + rng.uniform(-15, 20)))

    pattern_risk = rng.uniform(10, 55)
    if police in ("no", "?", ""):
        pattern_risk = min(100, pattern_risk + rng.uniform(10, 25))

    if fraud_reported == "Y":
        claim_risk = min(100, claim_risk + rng.uniform(10, 25))
        pattern_risk = min(100, pattern_risk + rng.uniform(10, 20))

    claim_risk = round(claim_risk, 1)
    customer_risk = round(customer_risk, 1)
    pattern_risk = round(pattern_risk, 1)
    overall = round(0.45 * claim_risk + 0.30 * customer_risk + 0.25 * pattern_risk, 1)

    if overall >= 65:
        risk_level = "High"
    elif overall >= 35:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    features_pool = [
        "total claim amount", "customer tenure", "damage severity",
        "number of vehicles", "police report availability",
        "bodily injuries", "type of incident", "annual premium",
        "deductible amount", "witness count", "occupation",
        "vehicle age", "incident location", "time of incident",
    ]
    top_features = rng.sample(features_pool, min(5, len(features_pool)))

    decision_trace = [
        f"Policy {claim_data.get('policy_number', 'N/A')} filed a {incident_type} claim for ${amount:,.0f}. Incident severity: {severity or 'minor damage'}.",
        f"Risk model scored this claim at {overall:.0f}/100 overall. Claim risk: {claim_risk:.0f}, Customer risk: {customer_risk:.0f}, Pattern risk: {pattern_risk:.0f}.",
        f"Top contributing factors: {', '.join(top_features[:3])}. {'Police report was not filed.' if police in ('no', '?', '') else 'Police report is on file.'}",
        f"Customer has been insured for {int(tenure)} months. {'Short tenure increases risk.' if tenure < 12 else 'Established customer relationship.'}",
        f"Overall risk classified as {risk_level}. " + {
            "High": "Escalation recommended — multiple risk signals detected.",
            "Medium": "Further investigation recommended before determination.",
            "Low": "Claim appears routine — standard processing advised.",
        }[risk_level],
    ]

    explanations = {
        "High": f"This {incident_type} claim for ${amount:,.0f} presents several elevated risk indicators. Key drivers: {', '.join(top_features[:3])}. Overall risk score of {overall:.0f}/100 warrants immediate investigator attention.",
        "Medium": f"This {incident_type} claim for ${amount:,.0f} shows mixed risk signals. Key factors: {', '.join(top_features[:3])}. Overall risk of {overall:.0f}/100 suggests further review is warranted.",
        "Low": f"This {incident_type} claim for ${amount:,.0f} appears consistent with typical filing patterns. Risk drivers minimal, score {overall:.0f}/100. Standard processing recommended.",
    }
    explanation = explanations[risk_level]

    ml_raw = {
        "fraud_probability": round(overall / 100, 4),
        "anomaly_score": round(rng.uniform(-0.3, 0.3), 4),
        "top_features": top_features,
    }

    if risk_level == "High":
        status = rng.choice(["analyzed", "analyzed", "escalated"])
    elif risk_level == "Medium":
        status = rng.choice(["analyzed", "analyzed", "deferred"])
    else:
        status = rng.choice(["analyzed", "cleared", "cleared"])

    analyzed_at = datetime.now().isoformat()

    conn.execute("""
        UPDATE claims SET
            status = ?, risk_level = ?,
            claim_risk_score = ?, customer_risk_score = ?,
            pattern_risk_score = ?, overall_risk_score = ?,
            ai_explanation = ?, decision_trace = ?,
            document_insights = ?, ml_raw = ?, analyzed_at = ?
        WHERE id = ?
    """, (
        status, risk_level, claim_risk, customer_risk, pattern_risk, overall,
        explanation, json.dumps(decision_trace),
        json.dumps({"summaries": [], "flags": [], "risk_hints": []}),
        json.dumps(ml_raw), analyzed_at, claim_id,
    ))

    if status in ("escalated", "cleared", "deferred"):
        action_map = {"escalated": "escalate", "cleared": "genuine", "deferred": "defer"}
        notes_map = {
            "escalated": "Multiple risk indicators warrant SIU review.",
            "cleared": "Claim consistent with normal patterns. Approved for processing.",
            "deferred": "Additional documentation requested before final determination.",
        }
        dec_id = f"DEC-{uuid.uuid4().hex[:8].upper()}"
        conn.execute(
            "INSERT INTO decisions (id, claim_id, user_id, action, notes) VALUES (?, ?, ?, ?, ?)",
            (dec_id, claim_id, user_id, action_map[status], notes_map[status])
        )


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------

def authenticate_by_username(username: str, password: str = "") -> Optional[Dict]:
    """Auth: resolve organization from username."""
    conn = get_conn()
    row = conn.execute("""
        SELECT u.id, u.username, u.display_name, u.role, u.password_hash,
               o.id as org_id, o.name as org_name
        FROM users u JOIN organizations o ON u.org_id = o.id
        WHERE u.username = ?
    """, (username,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    expected_hash = d.get("password_hash") or ""
    if expected_hash and _hash_password(password) != expected_hash:
        return None
    d.pop("password_hash", None)
    return d


def create_session(user_id: str, org_id: str) -> str:
    token = secrets.token_hex(32)
    expires = (datetime.now() + timedelta(hours=8)).isoformat()
    conn = get_conn()
    conn.execute(
        "INSERT INTO sessions (token, user_id, org_id, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, org_id, expires))
    conn.commit()
    conn.close()
    return token


def validate_session(token: str) -> Optional[Dict]:
    if not token:
        return None
    conn = get_conn()
    row = conn.execute("""
        SELECT s.user_id, s.org_id, s.expires_at,
               u.username, u.display_name, u.role, o.name as org_name
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        JOIN organizations o ON s.org_id = o.id
        WHERE s.token = ?
    """, (token,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    if datetime.fromisoformat(d["expires_at"]) < datetime.now():
        return None
    return d


def delete_session(token: str):
    conn = get_conn()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# CLAIMS
# ---------------------------------------------------------------------------

def create_claim(org_id: str, policy_number: str, claim_data: dict, source: str = "uploaded") -> str:
    claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
    conn = get_conn()
    conn.execute(
        "INSERT INTO claims (id, org_id, policy_number, claim_data, source, status) VALUES (?, ?, ?, ?, ?, ?)",
        (claim_id, org_id, policy_number, json.dumps(claim_data), source, "pending"))
    conn.commit()
    conn.close()
    return claim_id


def get_claims(org_id: str) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM claims WHERE org_id = ? ORDER BY created_at DESC", (org_id,)
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        for json_field in ("claim_data", "decision_trace", "document_insights", "ml_raw"):
            if d.get(json_field):
                try:
                    d[json_field] = json.loads(d[json_field])
                except:
                    pass
        results.append(d)
    return results


def get_claim(claim_id: str, org_id: str = None) -> Optional[Dict]:
    conn = get_conn()
    if org_id:
        row = conn.execute("SELECT * FROM claims WHERE id = ? AND org_id = ?", (claim_id, org_id)).fetchone()
    else:
        row = conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for json_field in ("claim_data", "decision_trace", "document_insights", "ml_raw"):
        if d.get(json_field):
            try:
                d[json_field] = json.loads(d[json_field])
            except:
                pass
    return d


def update_claim_analysis(claim_id: str, analysis: dict):
    conn = get_conn()
    conn.execute("""
        UPDATE claims SET
            status = 'analyzed',
            risk_level = ?, claim_risk_score = ?,
            customer_risk_score = ?, pattern_risk_score = ?,
            overall_risk_score = ?, ai_explanation = ?,
            decision_trace = ?, document_insights = ?,
            ml_raw = ?, analyzed_at = ?
        WHERE id = ?
    """, (
        analysis["risk_level"], analysis["claim_risk"],
        analysis["customer_risk"], analysis["pattern_risk"],
        analysis["overall_risk"], analysis["explanation"],
        json.dumps(analysis.get("decision_trace", [])),
        json.dumps(analysis.get("document_insights", {})),
        json.dumps(analysis.get("ml_raw", {})),
        datetime.now().isoformat(), claim_id,
    ))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# DOCUMENTS
# ---------------------------------------------------------------------------

def add_document(claim_id: str, filename: str, file_path: str) -> str:
    doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
    conn = get_conn()
    conn.execute(
        "INSERT INTO documents (id, claim_id, filename, file_path) VALUES (?, ?, ?, ?)",
        (doc_id, claim_id, filename, file_path))
    conn.commit()
    conn.close()
    return doc_id


def update_document_analysis(doc_id: str, ocr_text: str, summary: str, flags: list):
    conn = get_conn()
    conn.execute(
        "UPDATE documents SET ocr_text = ?, ai_summary = ?, ai_flags = ? WHERE id = ?",
        (ocr_text, summary, json.dumps(flags), doc_id))
    conn.commit()
    conn.close()


def get_claim_documents(claim_id: str) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM documents WHERE claim_id = ? ORDER BY uploaded_at", (claim_id,)
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        if d.get("ai_flags"):
            try:
                d["ai_flags"] = json.loads(d["ai_flags"])
            except:
                pass
        results.append(d)
    return results


# ---------------------------------------------------------------------------
# DECISIONS
# ---------------------------------------------------------------------------

def record_decision(claim_id: str, user_id: str, action: str, notes: str = "") -> str:
    dec_id = f"DEC-{uuid.uuid4().hex[:8].upper()}"
    conn = get_conn()
    conn.execute(
        "INSERT INTO decisions (id, claim_id, user_id, action, notes) VALUES (?, ?, ?, ?, ?)",
        (dec_id, claim_id, user_id, action, notes))
    status_map = {"escalate": "escalated", "genuine": "cleared", "defer": "deferred"}
    new_status = status_map.get(action, action)
    conn.execute("UPDATE claims SET status = ? WHERE id = ?", (new_status, claim_id))
    conn.commit()
    conn.close()
    return dec_id


def get_claim_decisions(claim_id: str) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT d.*, u.display_name as investigator_name
        FROM decisions d JOIN users u ON d.user_id = u.id
        WHERE d.claim_id = ?
        ORDER BY d.decided_at DESC
    """, (claim_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
