# Avia

**AI-powered claim investigation for insurance teams.**

Avia is a production-grade SaaS platform that triages insurance claims, scores risk across three dimensions using ML, and generates human-readable decision traces using Google Gemini. Investigators upload claim documents, review AI-generated insights, and record final decisions — all from a single interface.

---

## How It Works

1. **Upload a claim document** — PDF, image, or scanned form.
2. **AI extracts structured data** — Gemini multimodal reads the document and populates claim fields automatically.
3. **Risk assessment runs** — Three-bucket scoring (claim details, customer history, behavioral patterns) assigns a 0–100 risk score.
4. **Review the decision trace** — Step-by-step reasoning in plain English explains why the claim was flagged.
5. **Record a decision** — Escalate to SIU, clear as genuine, or defer for further review. Full audit trail.

Historical dataset claims (pre-loaded from CSV) can also be analyzed without document upload.

---

## Architecture

```
Vercel (single deployment)
├── React frontend (static build → Vercel CDN)
├── FastAPI serverless function (api/index.py → Python runtime)
│   ├── _db.py         — SQLite in /tmp (ephemeral, auto-seeded)
│   ├── _ml_engine.py  — XGBoost + Isolation Forest scoring
│   └── _genai_adapter.py — Gemini 2.5 Flash multimodal
├── models/            — Trained ML model files (bundled)
└── insurance_fraud.csv — Demo claim data (bundled)
```

- **Frontend**: React 19 (CRA) served as static files by Vercel CDN
- **Backend**: Single FastAPI app in `api/index.py` handling all `/api/*` routes
- **Database**: SQLite in `/tmp/avia.db` — ephemeral on Vercel, re-seeded on cold start
- **GenAI**: Google Gemini 2.5 Flash (mandatory) — document extraction, decision trace, investigator explanation
- **ML**: XGBoost + Isolation Forest with heuristic fallback if models exceed bundle limits

---

## Claim Sources

| Source | Label | How Created | Documents |
|--------|-------|-------------|-----------|
| Historical Dataset | `Historical Dataset` | Auto-seeded from `insurance_fraud.csv` on cold start | None — analyzed from existing structured data |
| Uploaded Document | `Uploaded Document` | Investigator uploads a document via the UI | AI extracts fields from the document |

---

## Demo Credentials

All demo accounts use password: **`avia2026`**

| Organization | Username | Name | Role |
|-------------|----------|------|------|
| Apex Insurance Co. | `jsmith` | John Smith | Investigator |
| Apex Insurance Co. | `mlee` | Maria Lee | Senior Investigator |
| Nova Assurance | `aturner` | Alex Turner | Investigator |
| Zenith General Insurance | `pshah` | Priya Shah | Investigator |
| Horizon Mutual | `dchen` | David Chen | Investigator |
| Reliance Shield | `rkumar` | Raj Kumar | Investigator |

Each organization sees only its own claims. Apex has the largest portfolio (~15 claims), others have 5–10 each.

---

## Deploy to Vercel

### Prerequisites

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

# Run with Vercel CLI (recommended — handles both frontend + API)
npx vercel dev

# Or run separately:
# Terminal 1: npm start
# Terminal 2: uvicorn api.index:app --reload --port 8000
```

---

## Project Structure

```
├── api/
│   ├── index.py              # FastAPI serverless handler (all routes)
│   ├── _db.py                # Database layer (5-org multi-tenant)
│   ├── _ml_engine.py         # ML scoring engine
│   └── _genai_adapter.py     # Gemini multimodal adapter
├── src/
│   ├── App.js                # React application
│   └── App.css               # Styles
├── models/                   # Trained ML model files
├── insurance_fraud.csv       # Demo claim dataset
├── vercel.json               # Vercel deployment config
├── requirements.txt          # Python dependencies
└── package.json              # Node.js dependencies
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key for document extraction and decision traces |
| `VERCEL` | Auto | Set automatically by Vercel — controls `/tmp/` path usage |

---

## Contact

For enterprise access inquiries: **karthikofficialmain@gmail.com**
