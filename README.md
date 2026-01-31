# JARZ-AI (RentRadar) — Spatio‑Temporal Rental Valuation (Hackathon)

This repo contains a **FastAPI + LangGraph** backend and a **Next.js** frontend.

The UX is a **chat interface**. As the user chats, the LLM agent can call tools (e.g. `get_rent_forecast`) and stream:
- **assistant text** into the chat panel
- **A2UI (Agent→UI) messages** into the insights side panel

> Important: Model code here is intentionally **PLACEHOLDER** (stub/pickle/http adapters). A teammate will swap in the real trained model later.
anshul is a good boy
## Repo layout (actual)

- `plan.md`: Hackathon plan (single source of truth — don’t edit unless explicitly intended)
- `run.ps1`: **PowerShell startup script** — runs backend + frontend with one command
- `backend/`: FastAPI API + LangGraph agents
  - `backend/app/main.py`: API routes + SSE streaming endpoints
  - `backend/app/agent/`: LangGraph graphs/nodes/state + tool definitions
  - `backend/app/model_adapter.py`: placeholder model adapters (stub/pickle/http)
  - `backend/app/a2ui_builder.py`: builds A2UI messages for the frontend to render
  - `backend/app/config.py`: environment configuration
  - `backend/app/llm_client.py`: OpenRouter LLM integration
  - `backend/app/scansan_client.py`: ScanSan property data API
- `frontend/`: Next.js app (chat + A2UI renderer)
  - `frontend/app/page.tsx`: main app with 5-page sidebar navigation
  - `frontend/hooks/useChatStream.ts`: consumes backend SSE `/api/chat/stream`
  - `frontend/components/A2UIRenderer.tsx`: maps A2UI components → React components
  - `frontend/components/`: visualization components
    - `SummaryCard.tsx`: P10/P50/P90 rental forecast display
    - `RentForecastChart.tsx`: 12-month trend chart
    - `DriversBar.tsx`: factor contribution bars
    - `NeighbourHeatmapMap.tsx`: spatial neighboring areas
    - `WhatIfControls.tsx`: scenario modeling inputs
    - `InsightsActions.tsx`: print/export/share/save buttons
    - `BudgetFilter.tsx`: search by budget and bedrooms
    - `ComparisonMode.tsx`: compare up to 3 areas
    - `InvestmentCalculator.tsx`: rental yield and ROI calculations
    - `InsightsDisclaimer.tsx`: data freshness and legal disclaimer
    - `ui/tooltip-custom.tsx`: custom hover tooltips

## Quickstart (Windows / PowerShell)

### Prereqs

- Python **3.11 or 3.12 recommended** (Python 3.14 may show dependency warnings)
- Node.js **18+** (20+ OK)

### Quick Start (Recommended)

**Use the automated startup script:**

```powershell
.\run.ps1
```

This script will:
1. Activate the Python virtual environment
2. Start the backend server on port 8000
3. Start the frontend dev server on port 3000
4. Open your browser to `http://localhost:3000`

**Requirements before running:**
- Backend virtual environment set up (see Manual Setup below)
- Frontend dependencies installed (`npm install` in frontend/)
- Environment variables configured (see Backend/Frontend environment sections below)

---

### Manual Setup (Alternative)

If you prefer to set up manually or need to troubleshoot:

#### 1) Backend setup

From repo root:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### Backend environment variables

- Copy `backend/.env.example` → `backend/.env` and fill in values **OR**
- Put the same variables in repo-root `.env`

The backend is configured to load env from both `backend/.env` and repo-root `.env`.

Required (for chat LLM):

- `OPENROUTER_API_KEY`
- `LLM_MODEL` (recommended: `openai/gpt-5-nano`)
- `LLM_BASE_URL` (recommended: `https://openrouter.ai/api/v1`)

Optional:

- `USE_SCANSAN=false` for offline/dev mode
- `SCANSAN_API_KEY` + `SCANSAN_BASE_URL` if you enable ScanSan calls

#### Run backend

On Windows, port 8000 can be blocked. We usually run on **8001**:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

Backend URL: `http://127.0.0.1:8001`

> **Note:** If using `run.ps1`, it starts the backend on port **8000** by default.

#### 2) Frontend setup

In a second terminal:

```powershell
cd frontend
npm install
```

#### Frontend environment variables

Set the backend URL in `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Run frontend

```powershell
npm run dev
```

Frontend URL: `http://localhost:3000`

## How to use (end-to-end)

1. Open `http://localhost:3000`
2. Ask something like:
   - “What’s the rent forecast for NW1?”
   - “Show me a 12‑month forecast for E14”
3. You should see:
   - Streaming assistant response in chat
   - A2UI insights on the right (Summary, Chart, Map, Drivers, etc.)

## API endpoints (backend)

- `POST /api/chat/stream` (SSE): main chat + A2UI streaming endpoint used by the frontend
- `POST /api/chat`: non-streaming chat (returns full response payload)
- `POST /api/query`: legacy non-chat “pipeline” endpoint
- `POST /api/stream`: legacy A2UI streaming endpoint (non-chat)

## Troubleshooting

### “WinError 10013” when starting Uvicorn on port 8000

Use another port (e.g. 8002/5000) and update `frontend/.env.local` accordingly.

### Chat shows no response even though backend returns 200

Common causes:
- Missing `OPENROUTER_API_KEY` (backend logs show something like `Bearer ` / illegal header)
- SSE parsing on Windows CRLF (`\r\n`) — frontend parsers must `.trim()` the `data:` payload before `JSON.parse()`

### Don’t commit secrets

Never commit `.env`, `.env.local`, or API keys. Rotate keys if they were ever committed.

## Contributor guide

See `AGENTS.md` for project-specific rules:
- how to add LangGraph tools safely
- how to emit A2UI components
- how the frontend consumes SSE and renders A2UI
- do/don’t rules to avoid breaking the demo
