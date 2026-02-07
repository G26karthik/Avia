"""
Avia — ML Engine
Three-bucket risk scoring: Claim Risk, Customer Risk, Pattern Risk.
Uses trained XGBoost + Isolation Forest models.
"""

import os
import json
import numpy as np
import warnings
from typing import Dict, List, Tuple, Optional

warnings.filterwarnings("ignore")

MODEL_DIR = "models"

# ---------------------------------------------------------------------------
# LOAD MODELS
# ---------------------------------------------------------------------------
_xgb_model = None
_iso_model = None
_scaler = None
_label_encoders = None
_metadata = None
_shap_explainer = None
_loaded = False


def _load_models():
    global _xgb_model, _iso_model, _scaler, _label_encoders, _metadata, _shap_explainer, _loaded
    if _loaded:
        return True
    try:
        import joblib
        _xgb_model = joblib.load(os.path.join(MODEL_DIR, "xgb_model.pkl"))
        _iso_model = joblib.load(os.path.join(MODEL_DIR, "iso_model.pkl"))
        _scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
        _label_encoders = joblib.load(os.path.join(MODEL_DIR, "label_encoders.pkl"))

        with open(os.path.join(MODEL_DIR, "metadata.json")) as f:
            _metadata = json.load(f)

        try:
            import shap
            _shap_explainer = shap.TreeExplainer(_xgb_model)
        except ImportError:
            print("SHAP not available — using feature importance fallback")

        _loaded = True
        return True
    except Exception as e:
        print(f"ML model loading failed: {e}")
        return False


# ---------------------------------------------------------------------------
# FEATURE NAME TRANSLATIONS
# ---------------------------------------------------------------------------
FEATURE_TRANSLATIONS = {
    "months_as_customer": "customer tenure",
    "age": "policyholder age",
    "policy_deductable": "deductible amount",
    "policy_annual_premium": "annual premium",
    "umbrella_limit": "umbrella coverage limit",
    "insured_sex": "gender",
    "insured_education_level": "education level",
    "insured_occupation": "occupation",
    "insured_relationship": "relationship status",
    "capital-gains": "reported capital gains",
    "capital-loss": "reported capital losses",
    "incident_type": "type of incident",
    "collision_type": "collision type",
    "incident_severity": "damage severity",
    "authorities_contacted": "authorities contacted",
    "number_of_vehicles_involved": "number of vehicles",
    "bodily_injuries": "bodily injuries",
    "witnesses": "witness count",
    "total_claim_amount": "total claim amount",
    "injury_claim": "injury claim portion",
    "property_claim": "property claim portion",
    "vehicle_claim": "vehicle claim portion",
    "incident_hour_of_the_day": "time of incident",
    "auto_make": "vehicle make",
    "auto_model": "vehicle model",
    "auto_year": "vehicle age",
    "policy_state": "policy state",
    "insured_hobbies": "policyholder hobbies",
    "incident_state": "incident location",
    "incident_city": "incident city",
    "property_damage": "property damage reported",
    "police_report_available": "police report availability",
}


def _translate(name: str) -> str:
    return FEATURE_TRANSLATIONS.get(name, name.replace("_", " "))


# ---------------------------------------------------------------------------
# PREPROCESSING
# ---------------------------------------------------------------------------

def _preprocess(claim_data: dict) -> np.ndarray:
    """Convert raw claim dict to feature vector."""
    feature_names = _metadata["feature_names"]
    cat_cols = _metadata["cat_cols"]
    row = {}
    for fname in feature_names:
        val = claim_data.get(fname, 0)
        if fname in cat_cols and _label_encoders and fname in _label_encoders:
            le = _label_encoders[fname]
            val_str = str(val) if val is not None else "MISSING"
            if val_str in le.classes_:
                val = le.transform([val_str])[0]
            else:
                val = 0
        else:
            try:
                val = float(val) if val is not None else 0.0
            except (ValueError, TypeError):
                val = 0.0
        row[fname] = val

    arr = np.array([[row[f] for f in feature_names]])
    return _scaler.transform(arr)


# ---------------------------------------------------------------------------
# THREE-BUCKET SCORING
# ---------------------------------------------------------------------------

# Feature groups for each bucket
CLAIM_FEATURES = {
    "total_claim_amount", "injury_claim", "property_claim", "vehicle_claim",
    "incident_type", "collision_type", "incident_severity", "incident_hour_of_the_day",
    "number_of_vehicles_involved", "bodily_injuries", "witnesses",
    "property_damage", "police_report_available", "authorities_contacted",
}

CUSTOMER_FEATURES = {
    "months_as_customer", "age", "insured_sex", "insured_education_level",
    "insured_occupation", "insured_hobbies", "insured_relationship",
    "capital-gains", "capital-loss", "policy_annual_premium",
    "policy_deductable", "umbrella_limit",
}

PATTERN_FEATURES = {
    "policy_state", "incident_state", "incident_city",
    "auto_make", "auto_model", "auto_year", "policy_csl",
    "insured_zip",
}


def _compute_bucket_scores(
    shap_values: np.ndarray, feature_names: list
) -> Tuple[float, float, float, List[str]]:
    """Compute three-bucket risk scores from SHAP values."""
    claim_score = 0.0
    customer_score = 0.0
    pattern_score = 0.0
    claim_total = 0.0
    customer_total = 0.0
    pattern_total = 0.0

    feature_contributions = []

    for i, fname in enumerate(feature_names):
        sv = shap_values[i]
        abs_sv = abs(sv)

        if fname in CLAIM_FEATURES:
            claim_score += max(0, sv)
            claim_total += abs_sv
        elif fname in CUSTOMER_FEATURES:
            customer_score += max(0, sv)
            customer_total += abs_sv
        else:
            pattern_score += max(0, sv)
            pattern_total += abs_sv

        if sv > 0.02:
            feature_contributions.append((_translate(fname), sv))

    # Normalize to 0-100
    max_contrib = max(claim_total, customer_total, pattern_total, 0.01)

    claim_norm = float(min(100, max(0, (claim_score / max(claim_total, 0.01)) * 100)))
    customer_norm = float(min(100, max(0, (customer_score / max(customer_total, 0.01)) * 100)))
    pattern_norm = float(min(100, max(0, (pattern_score / max(pattern_total, 0.01)) * 100)))

    # Sort top features by contribution
    feature_contributions.sort(key=lambda x: x[1], reverse=True)
    top_features = [f[0] for f in feature_contributions[:6]]

    return claim_norm, customer_norm, pattern_norm, top_features


def _compute_bucket_scores_fallback(
    fraud_prob: float, anomaly_score: float, claim_data: dict
) -> Tuple[float, float, float, List[str]]:
    """Heuristic bucket scoring when SHAP is unavailable."""
    base = fraud_prob * 100
    top_features = []

    # Claim risk heuristics
    amount = claim_data.get("total_claim_amount", 0)
    severity = str(claim_data.get("incident_severity", "")).lower()
    claim_risk = base * 0.8
    if amount > 50000:
        claim_risk = min(100, claim_risk + 20)
        top_features.append("total claim amount")
    if "total" in severity:
        claim_risk = min(100, claim_risk + 15)
        top_features.append("damage severity")

    # Customer risk heuristics
    tenure = claim_data.get("months_as_customer", 0)
    customer_risk = base * 0.5
    if tenure < 12:
        customer_risk = min(100, customer_risk + 25)
        top_features.append("customer tenure")

    # Pattern risk heuristics
    police = str(claim_data.get("police_report_available", "")).lower()
    pattern_risk = base * 0.4 + (anomaly_score * -30)
    if police in ("no", "?", ""):
        pattern_risk = min(100, pattern_risk + 15)
        top_features.append("police report availability")

    return (
        min(100, max(0, claim_risk)),
        min(100, max(0, customer_risk)),
        min(100, max(0, pattern_risk)),
        top_features[:6],
    )


# ---------------------------------------------------------------------------
# MAIN SCORING FUNCTION
# ---------------------------------------------------------------------------

def analyze_claim(claim_data: dict) -> Dict:
    """
    Run full ML analysis on a claim.
    Returns three-bucket scores, risk level, and top features.
    """
    if not _load_models():
        return _mock_analysis(claim_data)

    X = _preprocess(claim_data)

    # Fraud probability from XGBoost
    fraud_prob = float(_xgb_model.predict_proba(X)[0, 1])

    # Anomaly score from Isolation Forest
    anomaly_raw = float(_iso_model.decision_function(X)[0])

    # SHAP-based bucket scoring
    shap_vals = None
    top_features = []

    if _shap_explainer is not None:
        sv = _shap_explainer.shap_values(X)
        if isinstance(sv, list):
            shap_vals = sv[1][0] if len(sv) > 1 else sv[0][0]
        else:
            shap_vals = sv[0]
        claim_risk, customer_risk, pattern_risk, top_features = _compute_bucket_scores(
            shap_vals, _metadata["feature_names"]
        )
    else:
        claim_risk, customer_risk, pattern_risk, top_features = _compute_bucket_scores_fallback(
            fraud_prob, anomaly_raw, claim_data
        )

    # Overall risk = weighted combination
    overall = 0.45 * claim_risk + 0.30 * customer_risk + 0.25 * pattern_risk

    # Risk level
    if overall >= 65:
        risk_level = "High"
    elif overall >= 35:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # Next action
    if risk_level == "High":
        next_action = "Review Immediately"
    elif risk_level == "Medium":
        next_action = "Queue for Review"
    else:
        next_action = "Safe to Proceed"

    return {
        "claim_risk": float(round(claim_risk, 1)),
        "customer_risk": float(round(customer_risk, 1)),
        "pattern_risk": float(round(pattern_risk, 1)),
        "overall_risk": float(round(overall, 1)),
        "risk_level": risk_level,
        "next_action": next_action,
        "top_features": top_features,
        "ml_raw": {
            "fraud_probability": float(round(fraud_prob, 4)),
            "anomaly_score": float(round(anomaly_raw, 4)),
        },
    }


def _mock_analysis(claim_data: dict) -> Dict:
    """Fallback when models aren't available."""
    amount = claim_data.get("total_claim_amount", 0)
    tenure = claim_data.get("months_as_customer", 50)
    severity = str(claim_data.get("incident_severity", "")).lower()

    # Simple heuristic
    claim_risk = min(100, max(10, amount / 1000))
    customer_risk = min(100, max(10, 100 - tenure))
    pattern_risk = 40 if "total" in severity else 20

    overall = 0.45 * claim_risk + 0.30 * customer_risk + 0.25 * pattern_risk

    if overall >= 65:
        risk_level, next_action = "High", "Review Immediately"
    elif overall >= 35:
        risk_level, next_action = "Medium", "Queue for Review"
    else:
        risk_level, next_action = "Low", "Safe to Proceed"

    return {
        "claim_risk": round(claim_risk, 1),
        "customer_risk": round(customer_risk, 1),
        "pattern_risk": round(pattern_risk, 1),
        "overall_risk": round(overall, 1),
        "risk_level": risk_level,
        "next_action": next_action,
        "top_features": ["claim amount", "customer tenure", "damage severity"],
        "ml_raw": {"fraud_probability": overall / 100, "anomaly_score": 0.0},
    }
