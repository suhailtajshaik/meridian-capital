# meridian-capital

**Meridian** — a local-first, multi-agent personal finance advisor.
React + Vite frontend, FastAPI + LangGraph backend, OpenRouter LLM. Hackathon project.

A supervisor agent decomposes your questions and routes them to four
specialists (Debt Analyzer, Budget Coach, Savings Strategist, Payoff
Optimizer), all reasoning over a private document vault. Raw transactions
never leave your machine — only category aggregates are sent to the LLM.

## Demo

[![Meridian demo video](https://img.shields.io/badge/watch-demo-blue)](demo/C6-Group3-Meridian.mp4)

<video src="demo/C6-Group3-Meridian.mp4" controls width="720"></video>

> If the embedded player doesn't render on your viewer, download or open
> [`demo/C6-Group3-Meridian.mp4`](demo/C6-Group3-Meridian.mp4) directly.

## Run

### Run with Docker (recommended)

**Prerequisites:** Docker Desktop (or Docker Engine + Compose plugin).

1. Copy the env template and add your key:

   ```sh
   cp backend/.env.example backend/.env
   # open backend/.env and set OPENROUTER_API_KEY=sk-or-v1-...
   ```

   Get an OpenRouter key at https://openrouter.ai. Default model is
   `google/gemini-2.5-flash` — override via `OPENROUTER_MODEL`
   in `backend/.env` (e.g. `google/gemini-2.5-flash` for budget mode).

2. Start the full stack:

   ```sh
   docker compose up
   ```

   First run builds both images (a minute or two). Subsequent runs start in
   seconds. Both services support hot-reload — edit `backend/app/` or
   `frontend/src/` and changes appear immediately without restarting.

3. Open **http://localhost:5173** in your browser.

To stop: `Ctrl-C`, then `docker compose down`.

**Privacy note:** Both containers run entirely on your machine. The only
network egress is the LLM hop to OpenRouter. Your financial data stays local.

---

### Run without Docker

You need two terminals. Backend first (so the frontend can detect it on `/api/health`).

#### Terminal 1 — backend

```sh
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # then edit and add your OPENROUTER_API_KEY
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Get an OpenRouter key at https://openrouter.ai. Default model is
`google/gemini-2.5-flash` — override via `OPENROUTER_MODEL`
in `.env` (e.g. `google/gemini-2.5-flash` for budget mode).

#### Terminal 2 — frontend

```sh
cd frontend
npm install      # first time only
npm run dev
```

Opens at `http://localhost:5173`.

If the backend is offline, the UI shows a prominent error banner with
the docker command to bring it up. There is no mock fallback — the app
is fully driven by the live backend.

## Layout

```
meridian-capital/
├── backend/                   FastAPI + LangGraph agent engine
│   ├── requirements.txt · .env.example · README.md
│   └── app/
│       ├── main.py            FastAPI: /api/upload /api/chat (SSE) /api/snapshot /api/data /api/health
│       ├── config.py · llm.py
│       ├── agents/
│       │   ├── schemas.py     Pydantic v2 contracts (frontend depends on these shapes)
│       │   ├── base.py        SelfCorrectingAgent — retry + structured output
│       │   ├── debt_analyzer.py · budget_coach.py
│       │   ├── savings_strategist.py · payoff_optimizer.py
│       │   ├── supervisor.py  intent classifier
│       │   └── graph.py       LangGraph StateGraph + SqliteSaver checkpointing
│       ├── ingestion/
│       │   ├── parser.py      CSV / XLSX / PDF → DataFrame
│       │   ├── anonymizer.py  raw rows → category aggregates (LLM-safe)
│       │   └── tabular_rag.py NL → SQL over uploaded data
│       └── utils/math_engine.py   amortization, avalanche / snowball
│
├── frontend/                  React + Vite UI
│   └── src/
│       ├── main.jsx · App.jsx · sidebar.jsx
│       ├── chat.jsx · dashboard.jsx · documents.jsx · views.jsx
│       ├── charts.jsx · icons.jsx · tweaks-panel.jsx
│       ├── data.js            AGENT_META only (UI chrome — no financial data)
│       ├── lib/api.js · session.js
│       ├── hooks/useAgentStream.js · useFinancialData.js · useBackendStatus.js
│       └── index.css
│
├── sample_data/               seed CSVs to drag into the Documents tab
│   ├── chase_checking_apr2026.csv      (142 rows)
│   ├── capital_one_apr2026.csv         (41 rows)
│   ├── honda_auto_loan.csv             (24 rows · amortization)
│   ├── schwab_brokerage_q1.csv         (18 rows · holdings + activity)
│   ├── wells_mortgage_q1.csv           (3 rows · statement summary)
│   └── sofi_student_loan_apr.csv       (1 row · loan statement)
│
└── docs/
    ├── financial-advisor-hackathon-plan.md
    └── overnight-hackathon-plan-refined.md
```

## Demo path

1. **Documents** → drop the six files from `sample_data/`. The 5-step
   pipeline (Parse → Normalize → Redact → Embed → Index) is now driven by
   real upload progress. On success, the snapshot endpoint kicks off and
   the dashboard switches from "Demo data" to "Live data".
2. **Dashboard** → net worth, debt breakdown, budget 50/30/20, payoff
   timeline — all rendered from the live snapshot when present.
3. **Advisor chat** → ask *"I just got a $3,200 bonus. What should I do
   with it?"* — open the **"How I answered this"** trace under the reply
   to watch supervisor → debt → payoff → savings → synth in real time.
   Each `TraceEvent` is streamed via SSE as the LangGraph runs.
4. **Payoff** → toggle Snowball / Avalanche / Min — chart re-projects.
5. **Settings** → local-first vault status + security checklist + nuke
   button (calls `DELETE /api/data/:session_id`).

The orchestration trace under chat replies is the hackathon-judge moment —
it makes the multi-agent architecture *visible* instead of hidden behind
a polished output.

## Security model

- Backend binds `127.0.0.1` only. CORS locked to `http://localhost:5173`.
- Per-session SQLite at `backend/data/{session_id}.db`. Wiped via
  `DELETE /api/data/{session_id}`.
- Raw transactions never reach the LLM — `ingestion/anonymizer.py`
  aggregates to category sums and strips merchant / account / PII before
  the prompt is built.
- The LLM hop (OpenRouter) is the only network egress. The UI shows a
  consent banner explaining this.

## What's real today

| Layer | Status |
|---|---|
| File upload + parse (CSV / XLSX / PDF) | real |
| Anonymizer (raw → category aggregates) | real |
| Pydantic-structured agent outputs | real |
| Self-correcting retry loop on validation errors | real |
| LangGraph supervisor + 4 specialists | real |
| SSE trace streaming under chat replies | real |
| Tabular RAG (NL → SQL) | real |
| Frontend dashboard from live snapshot | real — empty states when no data, no mock fallback |
| Auth (JWT) | skipped per refined plan — session_id only |
| SQLCipher encryption | skipped — plain SQLite, wipe-on-demand |

Start backend, then frontend, then `Documents → Upload → Dashboard → Chat`.
