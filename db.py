"""
Avia — Database Layer (SQLite)
Manages organizations, users, claims, documents, and investigator decisions.
"""

import sqlite3
import os
import json
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DB_PATH = os.environ.get("AVIA_DB_PATH", "avia.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
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

    # Add password column if missing (migration-safe)
    try:
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        conn.commit()
    except:
        pass  # column already exists

    # Add source column if missing (migration-safe)
    try:
        conn.execute("ALTER TABLE claims ADD COLUMN source TEXT DEFAULT 'uploaded'")
        conn.execute("UPDATE claims SET source = 'dataset' WHERE source IS NULL")
        conn.commit()
    except:
        pass  # column already exists

    # Seed demo org + users if empty
    if conn.execute("SELECT COUNT(*) FROM organizations").fetchone()[0] == 0:
        org_id = "org-demo-001"
        pw_hash = _hash_password("avia2026")
        conn.execute("INSERT INTO organizations (id, name) VALUES (?, ?)",
                     (org_id, "Apex Insurance Co."))
        conn.execute(
            "INSERT INTO users (id, org_id, username, display_name, role, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
            ("user-001", org_id, "jsmith", "John Smith", "investigator", pw_hash))
        conn.execute(
            "INSERT INTO users (id, org_id, username, display_name, role, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
            ("user-002", org_id, "mlee", "Maria Lee", "senior_investigator", pw_hash))
        conn.commit()
    else:
        # Ensure existing users have passwords set
        pw_hash = _hash_password("avia2026")
        conn.execute("UPDATE users SET password_hash = ? WHERE password_hash IS NULL", (pw_hash,))
        conn.commit()

    conn.close()


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------

def _hash_password(password: str) -> str:
    """Hash a password with SHA-256. Simple but sufficient for demo."""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username: str, org_name: str, password: str = "") -> Optional[Dict]:
    """Auth: match username + org name + password."""
    conn = get_conn()
    row = conn.execute("""
        SELECT u.id, u.username, u.display_name, u.role, u.password_hash,
               o.id as org_id, o.name as org_name
        FROM users u JOIN organizations o ON u.org_id = o.id
        WHERE u.username = ? AND o.name = ?
    """, (username, org_name)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    # Validate password
    expected_hash = d.get("password_hash") or ""
    if expected_hash and _hash_password(password) != expected_hash:
        return None
    d.pop("password_hash", None)
    return d


def authenticate_by_username(username: str, password: str = "") -> Optional[Dict]:
    """Auth: resolve organization from username. Users belong to exactly one org."""
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
    """Create a session token for an authenticated user."""
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
    """Validate a session token. Returns user info or None."""
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
    """Delete a session token (logout)."""
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
            risk_level = ?,
            claim_risk_score = ?,
            customer_risk_score = ?,
            pattern_risk_score = ?,
            overall_risk_score = ?,
            ai_explanation = ?,
            decision_trace = ?,
            document_insights = ?,
            ml_raw = ?,
            analyzed_at = ?
        WHERE id = ?
    """, (
        analysis["risk_level"],
        analysis["claim_risk"],
        analysis["customer_risk"],
        analysis["pattern_risk"],
        analysis["overall_risk"],
        analysis["explanation"],
        json.dumps(analysis.get("decision_trace", [])),
        json.dumps(analysis.get("document_insights", {})),
        json.dumps(analysis.get("ml_raw", {})),
        datetime.now().isoformat(),
        claim_id,
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
    # Update claim status
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


# ---------------------------------------------------------------------------
# BULK SEED FROM CSV
# ---------------------------------------------------------------------------

def seed_claims_from_csv(org_id: str, csv_path: str, limit: int = 50):
    """Seed claims from the Kaggle dataset for demo purposes.
    Randomly pre-analyzes ~60% of claims so the UI shows a realistic mix of
    High / Medium / Low risk scores and varied statuses.
    """
    import pandas as pd
    import random
    import math

    conn = get_conn()
    existing = conn.execute("SELECT COUNT(*) FROM claims WHERE org_id = ?", (org_id,)).fetchone()[0]
    if existing > 0:
        conn.close()
        return existing

    df = pd.read_csv(csv_path)
    count = 0
    claim_ids = []

    for _, row in df.head(limit).iterrows():
        claim_data = row.to_dict()
        policy_num = str(claim_data.get("policy_number", f"POL-{count}"))
        claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
        conn.execute(
            "INSERT INTO claims (id, org_id, policy_number, claim_data, source, status) VALUES (?, ?, ?, ?, ?, ?)",
            (claim_id, org_id, policy_num, json.dumps(claim_data, default=str), "dataset", "pending"))
        claim_ids.append((claim_id, claim_data))
        count += 1

    conn.commit()

    # Pre-analyze a random subset so the dashboard shows realistic data
    random.seed(42)
    analyze_count = max(1, int(count * 0.6))
    to_analyze = random.sample(claim_ids, min(analyze_count, len(claim_ids)))

    for claim_id, claim_data in to_analyze:
        _seed_fake_analysis(conn, claim_id, claim_data, random)

    conn.commit()
    conn.close()
    return count


def _seed_fake_analysis(conn, claim_id: str, claim_data: dict, rng):
    """Generate realistic-looking pre-analyzed data for a seeded claim."""

    amount = float(claim_data.get("total_claim_amount", 0) or 0)
    tenure = float(claim_data.get("months_as_customer", 50) or 50)
    severity = str(claim_data.get("incident_severity", "")).lower()
    incident_type = str(claim_data.get("incident_type", "")).replace("_", " ")
    police = str(claim_data.get("police_report_available", "")).lower()
    fraud_reported = str(claim_data.get("fraud_reported", "")).upper()

    # --- Score generation (seeded with claim characteristics + randomness) ---
    # Base claim risk from amount and severity
    claim_risk = min(100, max(5, amount / 800 + rng.uniform(-10, 15)))
    if "total" in severity:
        claim_risk = min(100, claim_risk + rng.uniform(15, 30))
    elif "major" in severity:
        claim_risk = min(100, claim_risk + rng.uniform(5, 15))

    # Customer risk from tenure
    customer_risk = min(100, max(5, 80 - tenure * 0.5 + rng.uniform(-15, 20)))

    # Pattern risk
    pattern_risk = rng.uniform(10, 55)
    if police in ("no", "?", ""):
        pattern_risk = min(100, pattern_risk + rng.uniform(10, 25))

    # Boost scores for known-fraud rows in the dataset
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

    # --- Top features ---
    features_pool = [
        "total claim amount", "customer tenure", "damage severity",
        "number of vehicles", "police report availability",
        "bodily injuries", "type of incident", "annual premium",
        "deductible amount", "witness count", "occupation",
        "vehicle age", "incident location", "time of incident",
    ]
    top_features = rng.sample(features_pool, min(5, len(features_pool)))

    # --- Decision trace (pre-built narratives) ---
    decision_trace = [
        {
            "step": 1,
            "title": "Claim Intake Assessment",
            "detail": f"Policy {claim_data.get('policy_number', 'N/A')} filed a {incident_type} claim for ${amount:,.0f}. "
                      f"Incident severity: {severity or 'minor damage'}.",
        },
        {
            "step": 2,
            "title": "ML Risk Scoring",
            "detail": f"XGBoost fraud model scored this claim at {overall:.0f}/100 overall risk. "
                      f"Claim risk: {claim_risk:.0f}, Customer risk: {customer_risk:.0f}, Pattern risk: {pattern_risk:.0f}.",
        },
        {
            "step": 3,
            "title": "Key Risk Drivers",
            "detail": f"Top contributing factors: {', '.join(top_features[:3])}. "
                      f"{'Police report was not filed, which correlates with higher fraud rates.' if police in ('no', '?', '') else 'Police report is on file.'}",
        },
        {
            "step": 4,
            "title": "Customer Profile Review",
            "detail": f"Customer has been insured for {int(tenure)} months. "
                      f"{'Short tenure increases risk profile.' if tenure < 12 else 'Established customer relationship noted.'}",
        },
        {
            "step": 5,
            "title": "Risk Classification",
            "detail": f"Overall risk classified as {risk_level}. "
                      + ({
                          "High": "Escalation recommended — multiple risk signals detected.",
                          "Medium": "Further investigation recommended before determination.",
                          "Low": "Claim appears routine — standard processing advised.",
                      }[risk_level]),
        },
    ]

    # --- Explanation ---
    explanations = {
        "High": (
            f"This {incident_type} claim for ${amount:,.0f} presents several elevated risk indicators. "
            f"The ML model identified {', '.join(top_features[:3])} as the primary risk drivers. "
            f"With an overall risk score of {overall:.0f}/100, this claim warrants immediate investigator attention. "
            f"{'The absence of a police report is a notable concern.' if police in ('no', '?', '') else ''}"
        ),
        "Medium": (
            f"This {incident_type} claim for ${amount:,.0f} shows mixed risk signals. "
            f"Key factors include {', '.join(top_features[:3])}. "
            f"The overall risk score of {overall:.0f}/100 suggests further review is warranted "
            f"before a final determination."
        ),
        "Low": (
            f"This {incident_type} claim for ${amount:,.0f} appears consistent with typical filing patterns. "
            f"Risk drivers are minimal, with an overall score of {overall:.0f}/100. "
            f"Standard processing is recommended."
        ),
    }
    explanation = explanations[risk_level]

    ml_raw = {
        "fraud_probability": round(overall / 100, 4),
        "anomaly_score": round(rng.uniform(-0.3, 0.3), 4),
        "top_features": top_features,
    }

    # --- Pick a status (some analyzed, some decided) ---
    if risk_level == "High":
        status = rng.choice(["analyzed", "analyzed", "escalated"])
    elif risk_level == "Medium":
        status = rng.choice(["analyzed", "analyzed", "deferred"])
    else:
        status = rng.choice(["analyzed", "cleared", "cleared"])

    analyzed_at = datetime.now().isoformat()

    conn.execute("""
        UPDATE claims SET
            status = ?,
            risk_level = ?,
            claim_risk_score = ?,
            customer_risk_score = ?,
            pattern_risk_score = ?,
            overall_risk_score = ?,
            ai_explanation = ?,
            decision_trace = ?,
            document_insights = ?,
            ml_raw = ?,
            analyzed_at = ?
        WHERE id = ?
    """, (
        status, risk_level, claim_risk, customer_risk, pattern_risk, overall,
        explanation, json.dumps(decision_trace), json.dumps({"summaries": [], "flags": [], "risk_hints": []}),
        json.dumps(ml_raw), analyzed_at, claim_id,
    ))

    # If status is a decision (escalated/cleared/deferred), also record a decision
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
            (dec_id, claim_id, "user-001", action_map[status], notes_map[status])
        )
