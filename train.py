"""
Avia — ML Training Pipeline
Trains XGBoost (fraud probability) + Isolation Forest (anomaly detection)
Saves models + preprocessor to disk for the FastAPI backend.

Dataset: Kaggle "Insurance Fraud Detection" by arpan129
Expected CSV columns vary — this script auto-detects the fraud label column.
"""

import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.ensemble import IsolationForest
import xgboost as xgb
import joblib

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DATA_PATH = os.environ.get("AVIA_DATA_PATH", "insurance_fraud.csv")
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------------------
print("[1/6] Loading data …")
if not os.path.exists(DATA_PATH):
    print(f"ERROR: Dataset not found at '{DATA_PATH}'.")
    print("Please download from https://www.kaggle.com/datasets/arpan129/insurance-fraud-detection")
    print("and place the CSV in the project root as 'insurance_fraud.csv'.")
    sys.exit(1)

df = pd.read_csv(DATA_PATH)
print(f"  → {df.shape[0]} rows, {df.shape[1]} columns")

# ---------------------------------------------------------------------------
# 2. IDENTIFY TARGET COLUMN
# ---------------------------------------------------------------------------
print("[2/6] Identifying target column …")
fraud_col_candidates = [c for c in df.columns if "fraud" in c.lower()]
if not fraud_col_candidates:
    print("ERROR: No column containing 'fraud' found. Columns:", list(df.columns))
    sys.exit(1)

TARGET = fraud_col_candidates[0]
print(f"  → Target: '{TARGET}'")

# Map target to binary 0/1
unique_vals = df[TARGET].unique()
if set(unique_vals) <= {0, 1}:
    pass  # already binary
elif df[TARGET].dtype == object:
    pos_labels = {"y", "yes", "1", "true", "fraud"}
    df[TARGET] = df[TARGET].str.strip().str.lower().map(lambda x: 1 if x in pos_labels else 0)
else:
    df[TARGET] = (df[TARGET] > 0).astype(int)

print(f"  → Fraud distribution:\n{df[TARGET].value_counts().to_string()}")

# ---------------------------------------------------------------------------
# 3. FEATURE ENGINEERING
# ---------------------------------------------------------------------------
print("[3/6] Engineering features …")

# Drop columns that are identifiers or useless
drop_cols = []
for c in df.columns:
    if c == TARGET:
        continue
    if df[c].nunique() == len(df):  # unique ID-like
        drop_cols.append(c)
    elif df[c].nunique() == 1:  # constant
        drop_cols.append(c)
    elif "policy_number" in c.lower() or "id" == c.lower():
        drop_cols.append(c)

df.drop(columns=drop_cols, inplace=True, errors="ignore")
print(f"  → Dropped ID/constant cols: {drop_cols}")

# Separate features and target
y = df[TARGET].values
X = df.drop(columns=[TARGET])

# Encode categoricals
label_encoders = {}
cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
for col in cat_cols:
    le = LabelEncoder()
    X[col] = X[col].astype(str).fillna("MISSING")
    le.fit(X[col])
    X[col] = le.transform(X[col])
    label_encoders[col] = le

# Fill remaining NaN
X = X.fillna(0)

feature_names = X.columns.tolist()

# Scale for Isolation Forest (XGBoost doesn't need it, but we save the scaler)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"  → {len(feature_names)} features: {feature_names[:10]}{'…' if len(feature_names)>10 else ''}")

# ---------------------------------------------------------------------------
# 4. TRAIN XGBOOST
# ---------------------------------------------------------------------------
print("[4/6] Training XGBoost classifier …")
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

# Handle class imbalance
fraud_ratio = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

xgb_model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    scale_pos_weight=fraud_ratio,
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42,
)
xgb_model.fit(X_train, y_train)

y_pred = xgb_model.predict(X_test)
y_prob = xgb_model.predict_proba(X_test)[:, 1]

print("  → Classification Report:")
print(classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))
try:
    auc = roc_auc_score(y_test, y_prob)
    print(f"  → AUC-ROC: {auc:.4f}")
except:
    pass

# ---------------------------------------------------------------------------
# 5. TRAIN ISOLATION FOREST
# ---------------------------------------------------------------------------
print("[5/6] Training Isolation Forest …")
iso_model = IsolationForest(
    n_estimators=150,
    contamination=0.1,
    random_state=42,
)
iso_model.fit(X_scaled)
print("  → Done")

# ---------------------------------------------------------------------------
# 6. SAVE ARTIFACTS
# ---------------------------------------------------------------------------
print("[6/6] Saving models & artifacts …")

joblib.dump(xgb_model, os.path.join(MODEL_DIR, "xgb_model.pkl"))
joblib.dump(iso_model, os.path.join(MODEL_DIR, "iso_model.pkl"))
joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
joblib.dump(label_encoders, os.path.join(MODEL_DIR, "label_encoders.pkl"))

metadata = {
    "feature_names": feature_names,
    "cat_cols": cat_cols,
    "target_col": TARGET,
    "train_rows": int(len(y_train)),
    "test_rows": int(len(y_test)),
    "fraud_ratio": float(fraud_ratio),
}
with open(os.path.join(MODEL_DIR, "metadata.json"), "w") as f:
    json.dump(metadata, f, indent=2)

# Save a sample of raw data for the demo (first 200 rows)
sample = pd.read_csv(DATA_PATH).head(200)
sample.to_csv(os.path.join(MODEL_DIR, "sample_claims.csv"), index=False)

print(f"\n✅ All artifacts saved to '{MODEL_DIR}/'")
print("   Files: xgb_model.pkl, iso_model.pkl, scaler.pkl, label_encoders.pkl, metadata.json, sample_claims.csv")
print("\nNext: Run `uvicorn server:app --reload` to start the backend.")
