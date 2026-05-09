# 🚀 Overnight Hackathon Plan — Multi-Agent Financial Advisor
## Refined for Claude Code + OpenRouter + Existing Design

---

## Key Changes from v1

| Decision | Old Plan | Refined |
|---|---|---|
| **LLM** | Ollama (local) | **OpenRouter** via `langchain-openrouter` — faster, more capable models, one API key |
| **Dev Tool** | Manual coding | **Claude Code** as primary dev agent — you prompt, it builds |
| **Design** | From scratch | **Your existing Figma/design** — Claude Code implements it |
| **Security** | SQLCipher encryption | Simplified: **local SQLite + OpenRouter only** (user explicitly consents to LLM calls). No data persists beyond session unless user opts in |
| **Scope** | Full production | **Hackathon-viable MVP** — cut anything that doesn't demo well |

---

## Security Model (Revised for OpenRouter)

Since we're sending data to OpenRouter, be transparent:

```
┌─────────────────────────────────────────────────────┐
│                  USER'S LAPTOP                       │
│                                                      │
│  React UI ◄──► FastAPI (127.0.0.1:8000)              │
│                    │                                 │
│                    │  Only financial SUMMARIES        │
│                    │  sent to LLM, never raw data    │
│                    ▼                                 │
│              ┌───────────┐                           │
│              │ Pre-       │  Raw data stays local     │
│              │ processor  │  Aggregates + anonymizes  │
│              └─────┬─────┘  before LLM call          │
│                    │                                 │
│                    ▼                                 │
│    ───── NETWORK BOUNDARY ─────                      │
│                    │                                 │
│              OpenRouter API                          │
│              (LLM inference only)                    │
└─────────────────────────────────────────────────────┘
```

**Mitigations:**
1. **Pre-processing layer** — raw transactions get aggregated into categories/totals before hitting the LLM. The LLM sees "Credit card debt: $4,200 at 24.99% APR" not "Chase Sapphire ending 4829, transaction at Walmart..."
2. **No PII in prompts** — strip names, account numbers, merchant details. Send only financial structure
3. **Consent banner** — "Your financial summaries are processed via OpenRouter. Raw data stays on your device."
4. **Session-only storage** — SQLite in `/tmp`, wiped on exit unless user explicitly saves
5. **127.0.0.1 binding** — FastAPI never exposed to network

---

## OpenRouter LLM Setup

```python
# backend/app/llm.py

from langchain_openrouter import ChatOpenRouter

def get_llm(model: str = "anthropic/claude-sonnet-4-20250514"):
    """
    Recommended models for this project:
    - "anthropic/claude-sonnet-4-20250514"  → best structured output + tool calling
    - "google/gemini-2.5-flash"             → fastest, cheapest, good for budget
    - "meta-llama/llama-4-maverick"         → strong open model
    """
    return ChatOpenRouter(
        model=model,
        temperature=0.1,  # Low temp for financial accuracy
        # Structured output, streaming, tool calling all work natively
    )
```

```env
# .env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=anthropic/claude-sonnet-4-20250514
```

---

## Overnight Timeline (8-10 hours)

### Pre-Work: Setup (30 min) — YOU do this manually

```bash
# 1. Create project root
mkdir financial-advisor && cd financial-advisor

# 2. Scaffold frontend
npm create vite@latest frontend -- --template react
cd frontend && npm install && cd ..

# 3. Scaffold backend
mkdir -p backend/app/{agents,ingestion,db}
cd backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn langchain langgraph langchain-openrouter \
            pydantic pdfplumber openpyxl pandas sqlalchemy python-dotenv

# 4. Create .env
echo "OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE" > .env
echo "OPENROUTER_MODEL=anthropic/claude-sonnet-4-20250514" >> .env

# 5. Open Claude Code
claude
```

---

### Sprint 1: Backend Foundation (1.5 hrs)
**Claude Code prompt strategy: Give it ONE file at a time**

#### Prompt 1.1 — LLM Client
```
Create backend/app/llm.py:
- Use langchain-openrouter ChatOpenRouter
- Load model name from env OPENROUTER_MODEL, default "anthropic/claude-sonnet-4-20250514"
- Load API key from env OPENROUTER_API_KEY
- temperature=0.1
- Export a get_llm() function
```

#### Prompt 1.2 — Pydantic Schemas
```
Create backend/app/agents/schemas.py with these Pydantic v2 models:

1. DebtItem: name, category (enum: credit_card/student_loan/mortgage/auto_loan/
   personal_loan/medical/other), balance (>0), interest_rate (0-100, validator warns if >50),
   minimum_payment (>=0)

2. DebtAnalysis: debts list, total_debt, weighted_avg_interest,
   highest_priority_debt, monthly_minimum_total, debt_to_income_ratio (optional),
   risk_level (low/moderate/high/critical), summary string

3. BudgetAdvice: monthly_income, total_expenses, surplus_or_deficit,
   categories (list of {category, amount, percentage_of_income,
   recommendation: on_track/reduce/increase, suggested_amount}),
   top_3_savings_opportunities, actionable_steps, fifty_thirty_twenty dict

4. SavingsStrategy: emergency_fund_target, current_emergency_fund,
   months_of_runway, recommended_monthly_savings, savings_vehicles list,
   milestone_timeline list, strategy_narrative

5. PayoffPlan: strategy (avalanche/snowball/hybrid), monthly_budget_for_debt,
   payoff_order list, total_interest_saved_vs_minimum, debt_free_date,
   monthly_schedule (first 12 months), comparison dict (avalanche vs snowball)

All models should have clear Field descriptions for LLM format instructions.
```

#### Prompt 1.3 — Data Ingestion
```
Create backend/app/ingestion/parser.py:
- async parse_document(file: UploadFile) -> pd.DataFrame
- Support CSV, XLSX, PDF (via pdfplumber table extraction)
- Normalize column names to lowercase snake_case
- Auto-detect date columns and parse them
- Return clean DataFrame

Create backend/app/ingestion/anonymizer.py:
- anonymize_for_llm(df: pd.DataFrame) -> dict
- Aggregate transactions by category
- Strip merchant names, account numbers, PII
- Return summary dict like: {income: 9000, expenses: {rent: 1400, food: 250, ...},
  debts: [{type: "credit_card", balance: 4200, rate: 24.99, min_payment: 105}]}
- This is what gets sent to the LLM, never the raw data
```

#### Prompt 1.4 — Tabular RAG
```
Create backend/app/ingestion/tabular_rag.py:
- TabularRAG class with __init__(db_path, llm)
- ingest(df, table_name): load DataFrame into SQLite
- async query(natural_language_query) -> dict: convert NL → SQL → execute → return results
- Use langchain SQLDatabase for schema introspection
- Safety: wrap in read-only transaction, catch SQL errors
- Return {sql, columns, rows, count}
```

---

### Sprint 2: Agent Engine (2.5 hrs)
**This is the core — take your time with Claude Code here**

#### Prompt 2.1 — Self-Correcting Agent Base
```
Create backend/app/agents/base.py:
- SelfCorrectingAgent base class
- __init__(llm, output_schema: type[BaseModel], system_prompt: str)
- async run(user_data: dict, chat_history: list) -> BaseModel
- Implementation:
  1. Build messages with system prompt + format instructions from PydanticOutputParser
  2. Try up to 3 times
  3. On ValidationError, append the error as a HumanMessage asking LLM to fix
  4. On success, return parsed Pydantic model
  5. On final failure, raise with context
- Use with_structured_output() if the model supports it, fall back to PydanticOutputParser
```

#### Prompt 2.2 — Four Specialist Agents
```
Create these files, each as a subclass of SelfCorrectingAgent:

backend/app/agents/debt_analyzer.py:
- System prompt: expert debt analyst, categorize debts, calculate DTI,
  assess risk level, identify highest priority debt
- Output: DebtAnalysis schema
- Has access to tabular_rag as a tool for querying user's uploaded data

backend/app/agents/budget_coach.py:
- System prompt: personal budget coach, 50/30/20 rule analysis,
  identify spending leaks, actionable budget cuts
- Output: BudgetAdvice schema

backend/app/agents/savings_strategist.py:
- System prompt: savings advisor, emergency fund planning,
  recommend savings vehicles, create milestone timeline
- Output: SavingsStrategy schema

backend/app/agents/payoff_optimizer.py:
- System prompt: debt payoff optimization expert, compare avalanche vs snowball,
  calculate total interest under each strategy, project debt-free date,
  use amortization math
- Output: PayoffPlan schema
- Include actual financial math (not just LLM guessing) for amortization calculations
  in a utils/math_engine.py helper that the agent calls as a tool
```

#### Prompt 2.3 — LangGraph Orchestrator
```
Create backend/app/agents/graph.py:

LangGraph StateGraph with:
- State: messages, user_financial_data, debt_analysis, budget_advice,
  savings_strategy, payoff_plan, current_agent, needs_clarification
- Nodes: supervisor, debt_analyzer, savings_strategist, budget_coach,
  payoff_optimizer, clarify
- Supervisor node: uses LLM to classify user intent → routes to correct agent
- All agents return to supervisor after completing
- Clarify node: returns to user if question is ambiguous
- Entry point: supervisor
- Use SqliteSaver for checkpointing (multi-turn persistence)
- Compile with checkpointer

Add a "full_snapshot" mode: runs all 4 agents sequentially
and returns complete financial picture. Triggered on first upload.
```

#### Prompt 2.4 — FastAPI Server
```
Create backend/app/main.py:

FastAPI app with:
- CORS: only allow localhost:5173
- Host binding: 127.0.0.1 only

Endpoints:
1. POST /api/upload — accept CSV/XLSX/PDF, parse, store in SQLite,
   run anonymizer, trigger full_snapshot, return structured analysis
2. POST /api/chat — accept {messages, session_id}, stream SSE responses
   from LangGraph. Use StreamingResponse with async generator
3. GET /api/snapshot/{session_id} — return latest full analysis
4. DELETE /api/data/{session_id} — delete all session data
5. GET /api/health — return status

Each endpoint should have proper error handling and return structured JSON.
```

---

### Sprint 3: Frontend Implementation (2.5 hrs)
**Paste your design screenshots into Claude Code for reference**

#### Prompt 3.1 — Project Setup
```
In the frontend/ directory:
- Install: recharts, axios, lucide-react, tailwindcss, @tailwindcss/vite
- Configure Tailwind v4 with @tailwindcss/vite plugin
- Set up API client in src/lib/api.js pointing to http://localhost:8000
- Create the app shell matching this design: [paste your design screenshot]
```

#### Prompt 3.2 — Core Hooks
```
Create frontend/src/hooks/:

useAgentStream.js:
- SSE-based hook for streaming agent responses
- State: messages, isStreaming, activeAgent, error
- sendMessage(content, context) → POST to /api/chat as SSE
- Parse streaming events, update messages in real-time
- Track which agent is currently "thinking"

useFinancialData.js:
- uploadFile(file) → POST to /api/upload
- snapshot → GET /api/snapshot/:session
- deleteData() → DELETE /api/data/:session
- loading/error states
```

#### Prompt 3.3 — Dashboard Components
```
Build the dashboard matching my design. Components needed:

1. Dashboard.jsx — main layout grid
2. DebtBreakdown.jsx — donut/pie chart of debts by category (Recharts)
3. BudgetAnalysis.jsx — 50/30/20 bar chart + category breakdown
4. PayoffTimeline.jsx — line chart showing debt payoff projection over months
5. SavingsProjection.jsx — area chart of savings growth
6. SecurityBanner.jsx — sticky banner: "Your data stays on your device.
   Only anonymized summaries are sent for AI analysis."
7. AgentStatusIndicator.jsx — shows which agent is active with a pulse animation

Use the design I've provided for styling. [paste screenshots]
```

#### Prompt 3.4 — Chat Interface
```
Build ChatInterface.jsx:
- Full-height chat panel (sidebar or bottom drawer based on design)
- Message bubbles with agent identity (icon + name per agent)
- Streaming text effect for incoming messages
- Structured data cards inline when agent returns analysis
  (e.g., debt table, budget breakdown embedded in chat)
- Input field with send button
- "Agent thinking..." indicator with which agent name
- File upload drag-and-drop zone at the top
```

#### Prompt 3.5 — File Upload Flow
```
Build FileUpload.jsx:
- Drag-and-drop zone accepting CSV, XLSX, PDF
- File preview before upload (show first few rows for CSV/XLSX)
- Upload progress indicator
- On successful upload, auto-navigate to dashboard
- Show anonymization notice: "We'll analyze your data locally and
  only send category summaries to the AI"
```

---

### Sprint 4: Integration + Polish (1.5 hrs)

#### Prompt 4.1 — Wire Everything
```
Connect frontend to backend:
- FileUpload → POST /api/upload → on success, trigger full snapshot
- Dashboard reads from snapshot data and renders all charts
- Chat sends to /api/chat SSE endpoint
- Add session management (generate session_id on first load, store in sessionStorage)
- Error boundaries around all API calls
- Loading skeletons while agents process
```

#### Prompt 4.2 — Demo Data + Testing
```
Create backend/sample_data/ with:
1. sample_transactions.csv — 3 months of realistic transactions
   (income, rent, groceries, subscriptions, dining, etc.)
2. sample_debts.csv — 4 debts (credit card, student loan, car loan, medical)

Add a "Load Demo Data" button in the UI that auto-loads these files
so the hackathon demo doesn't depend on real uploads.
```

#### Prompt 4.3 — Final Polish
```
- Add loading animations between agent transitions
- Ensure all charts animate on data load
- Add a "Nuke My Data" button in settings
- Test the full flow: upload → auto-analyze → dashboard → chat → follow-up
- Fix any TypeErrors, API mismatches, or rendering issues
```

---

## Claude Code Tips for This Build

### Effective Prompting Pattern
```
# When starting a new file, give Claude Code the full context:
"Here's the Pydantic schema it needs to work with: [paste schema]
Here's the API endpoint it connects to: [paste endpoint]
Here's the design it should match: [paste screenshot]
Now create [component name]"

# When debugging:
"Run the backend with `uvicorn app.main:app --reload` and
hit POST /api/upload with the sample CSV.
Show me the error and fix it."

# When iterating:
"The debt chart renders but the data format from the API is
{debt_analysis: {debts: [...]}} not {debts: [...]}.
Update DebtBreakdown.jsx to handle the nested structure."
```

### Workflow
```
Terminal 1: Claude Code (your main dev agent)
Terminal 2: uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
Terminal 3: cd frontend && npm run dev
Browser:   http://localhost:5173 (keep open, Vite hot-reloads)
```

### Key Rules for Claude Code
1. **One file/feature per prompt** — don't ask for 5 things at once
2. **Paste your design** — screenshot → Claude Code for pixel-accurate implementation
3. **Test after each sprint** — don't stack 3 sprints of untested code
4. **Copy schemas between prompts** — Claude Code doesn't remember previous files. When building a frontend component, paste the relevant Pydantic schema so it knows the data shape
5. **Use `/compact` liberally** — keep context window clean in long sessions

---

## Project Dependency Files

### backend/requirements.txt
```
fastapi==0.115.12
uvicorn[standard]==0.34.3
langchain>=0.3.0
langgraph>=0.4.0
langchain-openrouter>=0.2.0
pydantic>=2.0
pydantic-settings>=2.0
sqlalchemy>=2.0
pandas>=2.0
pdfplumber>=0.11.0
openpyxl>=3.1.0
python-dotenv>=1.0
python-multipart>=0.0.9
```

### frontend/package.json (additional deps)
```json
{
  "dependencies": {
    "axios": "^1.7.0",
    "recharts": "^2.15.0",
    "lucide-react": "^0.383.0",
    "@tailwindcss/vite": "^4.0.0",
    "tailwindcss": "^4.0.0"
  }
}
```

---

## Makefile (for convenience)

```makefile
.PHONY: dev backend frontend setup

setup:
	cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

backend:
	cd backend && source venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

frontend:
	cd frontend && npm run dev

dev:
	@echo "Start backend and frontend in separate terminals:"
	@echo "  make backend"
	@echo "  make frontend"
```

---

## What to Cut if Running Behind

| Priority | Feature | Cut? |
|---|---|---|
| P0 | File upload + parsing | KEEP — core demo |
| P0 | Debt Analyzer agent | KEEP — most impressive |
| P0 | Dashboard with 1 chart | KEEP — visual wow |
| P0 | Chat interface | KEEP — shows multi-turn |
| P1 | Budget Coach agent | Keep if time |
| P1 | Payoff Optimizer | Keep if time |
| P2 | Savings Strategist | CUT first if behind |
| P2 | Tabular RAG (NL→SQL) | CUT — agents can work from pre-parsed data |
| P2 | Self-correcting retry loop | CUT — basic parsing is fine for demo |
| P3 | Security banner/nuke button | CUT — mention in slides |
| P3 | Animated transitions | CUT — functional > pretty |

**Minimum viable demo: Upload CSV → Debt Analyzer → Dashboard chart → Chat one question**

That's ~4 hours of focused Claude Code work. Everything else is gravy.
