# Avia

**AI-powered insurance fraud detection and claims investigation platform.**

Avia is a production-grade SaaS application that triages insurance claims, scores risk across three dimensions using XGBoost + Isolation Forest ML models, and generates human-readable decision traces using Google Gemini 2.5 Flash. Claims investigators can upload documents for multimodal AI extraction, review AI-generated insights with intake quality checks, generate SIU escalation packages, and record adjudication decisions — all from a single polished interface.

**Live Demo:** [https://avia-tau.vercel.app](https://avia-tau.vercel.app)

---

## Features

### Core Capabilities

- **Three-Bucket ML Risk Scoring** — Claim Risk, Customer Risk, and Pattern Risk scored independently (0–100), weighted into an overall fraud probability score
- **Multimodal Document Extraction** — Upload PDFs or images; Gemini 2.5 Flash reads documents directly using multimodal AI and extracts structured claim fields
- **GenAI Decision Traces** — Step-by-step reasoning narratives generated in plain English explaining why each claim was flagged
- **GenAI Investigator Explanations** — Concise, jargon-free summaries written as if briefing a senior investigator
- **Document Insights** — Per-document AI analysis identifying inconsistencies, key values, and risk flags

### Investigation Tools

- **Intake Quality Check** — Validates required/important fields before analysis, flags data inconsistencies (zero amounts, missing police reports, missing documents)
- **Escalation Package Generator** — One-click SIU handoff package with claim summary, risk assessment, reasoning trace, document evidence, and adjuster notes — copy to clipboard or download as JSON
- **Decision Audit Trail** — Full history of escalate/approve/defer decisions with timestamps, notes, and investigator attribution
- **Multi-Document Attachment** — Attach additional evidence to existing claims with real-time AI insights

### Dashboard & UX

- **Stats Dashboard** — Five-card overview (Total, High Risk, Medium Risk, Low Risk, Pending) with click-to-filter
- **Search & Filter** — Full-text search across claim ID, policy number, and incident type with risk-level filter pills
- **Tabbed Claim Detail** — Overview, Risk, Trace, Documents, Actions, and Escalation tabs
- **Toast Notification System** — Context-aware success/error/warning/info notifications with auto-dismiss
- **Session Persistence** — Browser session restoration via sessionStorage
- **Responsive Design** — Full mobile/tablet/desktop breakpoints

---

## How It Works

1. **Upload a claim document** — PDF, image, or scanned form (drag-and-drop or file picker)
2. **AI extracts structured data** — Gemini multimodal reads the document and populates claim fields automatically with strict extraction rules
3. **Run intake quality check** — Validates completeness of extracted data before proceeding
4. **AI risk assessment** — XGBoost fraud probability + Isolation Forest anomaly detection + SHAP-based three-bucket scoring
5. **Review the decision trace** — Step-by-step GenAI reasoning in plain English
6. **Record a decision** — Escalate to SIU, approve as genuine, or defer for more info — full audit trail
7. **Generate escalation package** — Comprehensive investigation bundle ready for SIU handoff

Historical dataset claims (pre-loaded from CSV) can also be analyzed without document upload.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Vercel                         │
│  ┌──────────────┐   ┌────────────────────────┐  │
│  │  React 19     │   │  FastAPI (Serverless)  │  │
│  │  Static Build │   │  api/index.py          │  │
│  │  → Vercel CDN │   │  ├── _db.py (SQLite)   │  │
│  │               │   │  ├── _ml_engine.py     │  │
│  │  Single-file  │   │  └── _genai_adapter.py │  │
│  │  App.js +     │   │                        │  │
│  │  App.css      │   │  Models: XGBoost +     │  │
│  │               │   │  Isolation Forest      │  │
│  └──────┬───────┘   └──────────┬─────────────┘  │
│         │  fetch /api/*        │                  │
│         └──────────────────────┘                  │
└─────────────────────────────────────────────────┘
                      │
                      ▼
              Google Gemini 2.5 Flash
              (Multimodal GenAI)
```

| Layer | Technology | Details |
|-------|-----------|---------|
| **Frontend** | React 19 (CRA) | Single-file component architecture, CSS custom properties design system |
| **Backend** | FastAPI 0.115+ | Dual deployment: `server.py` (local) + `api/index.py` (Vercel serverless) |
| **Database** | SQLite + WAL mode | `/tmp/avia.db` on Vercel (ephemeral, auto-seeded), `avia.db` locally |
| **ML Engine** | XGBoost + Isolation Forest | SHAP-based feature importance, three-bucket scoring, heuristic fallback |
| **GenAI** | Google Gemini 2.5 Flash | Multimodal document extraction, decision trace, explanations, document insights |
| **Auth** | Token-based sessions | SHA-256 password hashing, 8-hour session tokens, Bearer auth |

---

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/api/auth/login` | Authenticate user (org resolved from account) | No |
| `POST` | `/api/auth/logout` | Invalidate session | Yes |
| `GET` | `/api/auth/me` | Get current user info | Yes |
| `GET` | `/api/claims` | List all claims for user's organization | Yes |
| `GET` | `/api/claims/{id}` | Get full claim detail with analysis, documents, decisions | Yes |
| `POST` | `/api/claims` | Create a new claim manually | Yes |
| `POST` | `/api/claims/upload` | Upload documents → multimodal extraction → create claim | Yes |
| `POST` | `/api/claims/{id}/documents` | Attach additional documents to existing claim | Yes |
| `GET` | `/api/claims/{id}/documents` | Get documents list for a claim | Yes |
| `POST` | `/api/claims/{id}/analyze` | Run ML + GenAI full analysis | Yes |
| `POST` | `/api/claims/{id}/decide` | Record escalate/approve/defer decision | Yes |
| `GET` | `/api/claims/{id}/intake-check` | Validate field completeness before analysis | Yes |
| `GET` | `/api/claims/{id}/escalation-package` | Generate SIU escalation package | Yes |
| `GET` | `/api/health` | Health check (GenAI + ML status) | No |
| `POST` | `/api/seed` | Seed demo claims from CSV (idempotent) | No |

---

## Claim Sources

| Source | Badge | How Created | Documents |
|--------|-------|-------------|-----------|
| Historical Dataset | `Dataset` | Auto-seeded from `insurance_fraud.csv` on cold start (~50 claims, ~60% pre-analyzed) | None — analyzed from existing structured data |
| Uploaded Document | `Uploaded` | Investigator uploads via UI → Gemini extracts fields | AI extraction + per-document insights |

---

## ML Pipeline

### Training (`train.py`)

```
insurance_fraud.csv
       │
       ▼
  Feature Engineering
  (Label Encoding + StandardScaler)
       │
       ├── XGBoost Classifier → Fraud Probability (0–1)
       │
       └── Isolation Forest → Anomaly Score
       │
       ▼
  models/
  ├── xgb_model.pkl
  ├── iso_model.pkl
  ├── scaler.pkl
  ├── label_encoders.pkl
  └── metadata.json
```

### Inference (`ml_engine.py`)

Three-bucket scoring from SHAP values:

| Bucket | Features | Weight |
|--------|----------|--------|
| **Claim Risk** | Amount, severity, incident type, vehicles, injuries, witnesses, police report | 45% |
| **Customer Risk** | Tenure, age, education, occupation, premium, deductible, umbrella limit | 30% |
| **Pattern Risk** | Location, vehicle details, policy CSL, ZIP code | 25% |

Risk thresholds: **High** ≥ 65 · **Medium** ≥ 35 · **Low** < 35

---

## Demo Credentials

All demo accounts use password: **`avia2026`**

| Organization | Username | Name | Role |
|-------------|----------|------|------|
| Apex Insurance Co. | `jsmith` | John Smith | Investigator |
| Apex Insurance Co. | `mlee` | Maria Lee | Senior Investigator |

---

## Deploy to Vercel

### Prerequisites

- **Live instance:** [https://avia-tau.vercel.app](https://avia-tau.vercel.app)
- [Vercel account](https://vercel.com) (free tier works)
- Google Gemini API key ([Get one](https://aistudio.google.com/apikey))

### Steps

1. **Push the repo** to GitHub (or any Git provider Vercel supports).

2. **Import the project** in Vercel Dashboard → "Add New Project" → select the repo.

3. **Set environment variables** in Vercel project settings:

   | Variable | Value |
   |----------|-------|
   | `GEMINI_API_KEY` | Your Google Gemini API key |

4. **Deploy.** Vercel auto-detects CRA for the frontend build and Python for the serverless function. No additional configuration needed — `vercel.json` handles routing.

5. **Open your deployment URL** and sign in with any demo credentials above.

### Local Development

```bash
# Install frontend dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt

# Set your API key
export GEMINI_API_KEY="your-key-here"    # macOS/Linux
$env:GEMINI_API_KEY = "your-key-here"    # PowerShell

# Option 1: Single command startup (PowerShell)
.\start.ps1

# Option 2: Vercel CLI (handles both frontend + API)
npx vercel dev

# Option 3: Run separately
# Terminal 1: npm start          → React dev server on :3000
# Terminal 2: uvicorn server:app --reload --port 8000
```

---

## Project Structure

```
avia/
├── server.py                 # FastAPI backend (local development, 877 lines)
├── db.py                     # SQLite database layer (multi-tenant, sessions, 601 lines)
├── ml_engine.py              # ML scoring engine (XGBoost + SHAP, 340 lines)
├── genai_adapter.py          # Gemini 2.5 Flash adapter (multimodal, 368 lines)
├── ocr_engine.py             # Legacy file (unused - multimodal AI is primary)
├── train.py                  # ML training pipeline (187 lines)
├── test_api.py               # API integration tests (129 lines)
├── start.ps1                 # One-command startup script (PowerShell)
│
├── api/                      # Vercel serverless deployment
│   ├── index.py              # FastAPI handler (mirrors server.py)
│   ├── _db.py                # Database layer (Vercel variant, /tmp paths)
│   ├── _ml_engine.py         # ML engine (Vercel variant)
│   └── _genai_adapter.py     # GenAI adapter (Vercel variant)
│
├── src/                      # React frontend
│   ├── App.js                # All components (single-file architecture)
│   └── App.css               # Design system (CSS custom properties)
│
├── models/                   # Trained ML model artifacts
│   ├── metadata.json         # Feature names, categorical columns
│   └── sample_claims.csv     # Sample data
│
├── build/                    # Production React build (Vercel CDN)
├── uploads/                  # Document storage (local dev)
├── insurance_fraud.csv       # Kaggle fraud detection dataset
├── requirements.txt          # Python dependencies
├── package.json              # Node.js dependencies (React 19)
└── vercel.json               # Vercel routing & function config
```

---

## Design System

The UI uses a warm professional insurance aesthetic with CSS custom properties:

| Token | Value | Usage |
|-------|-------|-------|
| `--primary` | `#0d6e6e` (Deep Teal) | Navigation, buttons, active states |
| `--accent` | `#e8553d` (Warm Coral) | CTAs, highlights, badges |
| `--bg` | `#f7f8fb` | Page background |
| `--surface` | `#ffffff` | Cards, modals |
| `--text` | `#1a2332` | Primary text |
| `--radius-xl` | `24px` | Cards, modals |
| `--radius-full` | `9999px` | Buttons, pills, badges |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key for document extraction, decision traces, and explanations |
| `AVIA_DB_PATH` | No | Custom SQLite database path (default: `avia.db` or `/tmp/avia.db` on Vercel) |
| `AVIA_CSV_PATH` | No | Path to claims dataset CSV (default: `insurance_fraud.csv`) |
| `VERCEL` | Auto | Set automatically by Vercel — controls ephemeral `/tmp/` path usage |

---

## Tech Stack

| Category | Technology | Version |
|----------|-----------|---------|
| Frontend | React | 19.2 |
| Bundler | Create React App | 5.0 |
| Backend | FastAPI | Latest |
| Language | Python | 3.10+ |
| Database | SQLite | 3 (WAL mode) |
| ML | XGBoost, scikit-learn, SHAP | Latest |
| GenAI | Google Gemini 2.5 Flash | `google-genai` SDK |
| Deployment | Vercel | Serverless Functions |

---

## Contact

For enterprise access inquiries: **karthikofficialmain@gmail.com**
