# meridian-capital

**Meridian** is a local-first, multi-agent personal finance advisor.
It pairs a React + Vite frontend with a FastAPI + LangGraph backend, using an OpenRouter LLM for reasoning.
This repo demonstrates a hackathon-grade architecture for safe financial advice: private local data ingestion, structured agent outputs, and visible multi-agent reasoning.

---

## What this project is

Meridian helps users explore personal finance using uploaded statements and transaction data.
The application includes:

- a document ingestion experience for CSV/XLSX/PDF financial exports
- a local session vault stored in SQLite
- a private analytics snapshot for net worth, budgets, and payoff plans
- a conversational advisor powered by a supervisor and specialist agents
- a streaming trace UI that exposes how decisions are routed and composed

The system is built so that raw financial statements stay local and only LLM-safe summary data is shared with the model.

---

## Architecture overview

The architecture diagram is available in `architecture.excalidraw` at the repo root. Open it to view the frontend/backend flow, agent orchestration, privacy boundaries, and session storage model.

### High-level flow

1. User uploads financial documents in the frontend.
2. The backend parses files and normalizes raw rows into a standard dataset.
3. A privacy layer anonymizes and aggregates transactions into category-level facts.
4. The local session database stores the clean snapshot and queryable tables.
5. The user asks the advisor a question.
6. The supervisor agent routes the request to specialist agents.
7. Structured agent outputs are generated, validated, and streamed back via SSE.
8. The frontend renders the advice, dashboard, and orchestration trace.

### Components

- **Frontend**: React + Vite app serving the user interface, upload experience, dashboard, chat, and visual trace.
- **Backend**: FastAPI app exposing `api/upload`, `api/chat`, `api/snapshot`, `api/data`, and health endpoints.
- **Agents**: LangGraph-based supervisor + specialist agents for debt, budget, savings, and payoff reasoning.
- **Ingestion**: parser, anonymizer, and tabular RAG components that turn uploaded statements into safe, queryable data.
- **Session storage**: per-session SQLite files under `backend/data/{session_id}.db`.

### Agent architecture

Meridian uses a layered multi-agent design:

- `supervisor.py` routes questions to the right specialist(s) and composes final answers.
- `debt_analyzer.py` analyzes debts, interest, and payoff risk.
- `budget_coach.py` evaluates spending, budgets, and savings opportunities.
- `savings_strategist.py` recommends cash reserves, investments, and buffers.
- `payoff_optimizer.py` compares payoff strategies like avalanche, snowball, and minimum payments.

The backend also includes `base.py` with a self-correcting agent wrapper: it validates outputs and retries when LLM responses are malformed.

### Data privacy model

- The backend binds only to `127.0.0.1`.
- CORS permits only `http://localhost:5173`.
- Raw uploaded transactions are parsed locally and never sent directly to the LLM.
- `ingestion/anonymizer.py` converts raw rows into category aggregates and strips PII details.
- Only aggregated, LLM-safe facts are used for model prompts.
- The only outbound network call is to the OpenRouter LLM service.

---

## Run the app

### Run with Docker (recommended)

Prerequisites: Docker Desktop or Docker Engine with Compose plugin.

1. Copy the backend env template and configure your key:

   ```sh
   cp backend/.env.example backend/.env
   # edit backend/.env and set OPENROUTER_API_KEY=sk-or-v1-...
   ```

2. Start the full stack:

   ```sh
   docker compose up
   ```

3. Open `http://localhost:5173` in your browser.

To stop the stack, press `Ctrl-C` and run:

```sh
docker compose down
```

### Run without Docker

Open two terminal windows.

#### Backend

```sh
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit backend/.env and set OPENROUTER_API_KEY
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Frontend

```sh
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` once both services are running.

---

## File structure

```
meridian-capital/
├── backend/                       FastAPI + LangGraph finance agent engine
│   ├── Dockerfile
│   ├── README.md
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py                FastAPI routes and SSE chat API
│       ├── config.py              app configuration and environment loading
│       ├── llm.py                 OpenRouter / model request helpers
│       ├── agents/
│       │   ├── base.py            self-correcting agent wrapper + structured output validation
│       │   ├── supervisor.py      intent routing and orchestration
│       │   ├── debt_analyzer.py
│       │   ├── budget_coach.py
│       │   ├── savings_strategist.py
│       │   ├── payoff_optimizer.py
│       │   ├── graph.py           LangGraph StateGraph with SqliteSaver checkpointing
│       │   └── schemas.py         Pydantic v2 contracts used by both backend and frontend
│       ├── ingestion/
│       │   ├── parser.py          CSV / XLSX / PDF parsing into normalized tables
│       │   ├── anonymizer.py       raw → category aggregates for privacy-safe prompts
│       │   └── tabular_rag.py      natural language SQL query layer over uploaded data
│       └── utils/
│           └── math_engine.py     amortization, payoff projections, avalanche / snowball math
│
├── frontend/                      React + Vite user interface
│   ├── Dockerfile
│   ├── README.md
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx              application entrypoint
│       ├── App.jsx               app shell, navigation, and layout
│       ├── sidebar.jsx           main navigation menu
│       ├── chat.jsx              advisor chat panel + trace rendering
│       ├── dashboard.jsx         live snapshot dashboard views
│       ├── documents.jsx         document upload / ingestion UI
│       ├── views.jsx             detail views for debt, savings, budget, payoff, settings
│       ├── charts.jsx            visualizations and charts
│       ├── icons.jsx             inline icon components
│       ├── tweaks-panel.jsx      design / debug tweak controls
│       ├── data.js               static metadata and seed UI data
│       ├── lib/api.js            backend API client helpers
│       ├── lib/session.js        session management helpers
│       └── hooks/
│           ├── useAgentStream.js
│           ├── useBackendStatus.js
│           └── useFinancialData.js
│
├── sample_data/                  example files for the demo flow
├── docs/                         planning notes and hackathon docs
└── demo/                         video walkthrough and demo assets
```

---

## User flow

1. Open the app and go to the `Documents` tab.
2. Drag the sample files from `sample_data/` into the upload area.
3. Wait for ingestion to complete and a snapshot to appear.
4. Visit `Dashboard` to review net worth, debt breakdown, budget guidance, and payoff projections.
5. Ask the advisor a question in the `Advisor chat` view.
6. Expand the trace under the answer to inspect supervisor decisions and specialist reasoning.

---

## Notes for developers

- `frontend/src/data.js` contains UI metadata and seeded persona/chat examples. The app uses real backend data once ingestion is complete.
- `backend/app/agents/schemas.py` defines the API contracts shared by the frontend and backend.
- `backend/app/agents/graph.py` manages LangGraph state, checkpoints, and replayable agent execution.
- `backend/app/ingestion/tabular_rag.py` adds a natural language SQL layer for querying uploaded tables.
- The agent trace is streamed from the backend as Server-Sent Events (SSE) and displayed live in the chat panel.

---

## Security and privacy

- All data is processed locally on the machine running the app.
- The only external network access is the OpenRouter LLM endpoint.
- Session data is stored in plain SQLite under `backend/data/`, with a wipe endpoint available.
- No JWT auth is implemented; the current app uses session IDs only.

---

## Current status

| Capability | Status |
|---|---|
| Document upload and parse | implemented |
| Data anonymization for LLM prompts | implemented |
| Multi-agent supervisor + specialist reasoning | implemented |
| Structured agent output validation | implemented |
| SSE stream of agent traces | implemented |
| Dashboard snapshot rendering | implemented |
| Auth / encryption | intentionally skipped |

---

## Helpful links

- `backend/README.md` — backend developer notes
- `frontend/README.md` — frontend run/build notes
- `docs/` — planning and architecture notes
- `sample_data/` — demo files to upload
- `demo/` — video walkthrough
