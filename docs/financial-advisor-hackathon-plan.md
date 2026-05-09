# 💰 Multi-Agent Financial Advisor — Hackathon Plan

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    USER'S LAPTOP ONLY                    │
│                  (Zero Cloud Exposure)                   │
│                                                         │
│  ┌──────────────────────┐   ┌────────────────────────┐  │
│  │   React + Vite UI    │   │   Python Agent Engine   │  │
│  │   (Port 5173)        │◄─►│   FastAPI (Port 8000)   │  │
│  │                      │   │                         │  │
│  │  • Dashboard         │   │  ┌───────────────────┐  │  │
│  │  • Chat Interface    │   │  │   LangGraph        │  │  │
│  │  • Visualizations    │   │  │   Orchestrator     │  │  │
│  │  • File Upload       │   │  │                    │  │  │
│  └──────────────────────┘   │  │  ┌──────────────┐ │  │  │
│                             │  │  │ Debt Analyzer │ │  │  │
│  ┌──────────────────────┐   │  │  ├──────────────┤ │  │  │
│  │   SQLite (local)     │   │  │  │ Savings Guru │ │  │  │
│  │   • User financials  │   │  │  ├──────────────┤ │  │  │
│  │   • Chat history     │   │  │  │ Budget Coach │ │  │  │
│  │   • Agent state      │   │  │  ├──────────────┤ │  │  │
│  └──────────────────────┘   │  │  │ Payoff Opt.  │ │  │  │
│                             │  │  └──────────────┘ │  │  │
│  ┌──────────────────────┐   │  └───────────────────┘  │  │
│  │   Local LLM (Ollama) │   │                         │  │
│  │   or API key in .env │   └────────────────────────┘  │
│  └──────────────────────┘                               │
└─────────────────────────────────────────────────────────┘
```

---

## 1. Security-First Design (Non-Negotiable)

Since user financial data must NEVER leave the laptop:

| Layer | Strategy |
|---|---|
| **LLM** | Option A: **Ollama** running locally (llama3.1, mistral, etc.) — zero network calls. Option B: API key in `.env` with explicit user consent banner ("Your data is sent to OpenAI/Anthropic for processing") |
| **Storage** | SQLite file on disk. No cloud DB. Encrypted at rest with `sqlcipher` |
| **Network** | FastAPI binds to `127.0.0.1` only. CORS locked to `localhost:5173`. No external endpoints |
| **File Processing** | All document parsing (PDF, CSV, XLSX) happens in-process via Python libs. Never uploaded anywhere |
| **Session** | JWT tokens with short expiry, stored in httpOnly cookies. No localStorage for sensitive data |
| **Cleanup** | Optional "nuke my data" button that deletes SQLite + all cached agent state |

### `.env` Structure
```env
# Choose one:
LLM_PROVIDER=ollama          # or "openai" or "anthropic"
LLM_MODEL=llama3.1:8b        # or "gpt-4o-mini" or "claude-sonnet-4-20250514"

# Only needed if not using Ollama:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Security
JWT_SECRET=<random-256bit>
SQLITE_ENCRYPTION_KEY=<random-256bit>
BIND_HOST=127.0.0.1
```

---

## 2. Project Structure

```
financial-advisor/
├── frontend/                    # React + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx        # Main financial dashboard
│   │   │   ├── ChatInterface.jsx    # Multi-turn agent chat
│   │   │   ├── FileUpload.jsx       # Document ingestion
│   │   │   ├── DebtVisualizer.jsx   # Debt payoff timeline chart
│   │   │   ├── BudgetBreakdown.jsx  # Income vs spending donut
│   │   │   ├── SavingsProjection.jsx # Savings growth over time
│   │   │   └── SecurityBanner.jsx   # "Your data stays local" badge
│   │   ├── hooks/
│   │   │   ├── useAgentStream.js    # SSE hook for streaming agent responses
│   │   │   └── useFinancialData.js  # SWR/React Query for local API
│   │   ├── lib/
│   │   │   └── api.js               # Axios client → localhost:8000
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/                     # Python Agent Engine
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Settings via pydantic-settings
│   │   ├── security.py              # JWT, encryption, CORS
│   │   │
│   │   ├── agents/
│   │   │   ├── graph.py             # LangGraph orchestrator (supervisor)
│   │   │   ├── debt_analyzer.py     # Debt analysis agent
│   │   │   ├── savings_strategist.py # Savings strategy agent
│   │   │   ├── budget_coach.py      # Budget advice agent
│   │   │   ├── payoff_optimizer.py  # Debt payoff optimization agent
│   │   │   └── schemas.py           # Pydantic structured output models
│   │   │
│   │   ├── ingestion/
│   │   │   ├── parser.py            # PDF/CSV/XLSX → structured data
│   │   │   ├── categorizer.py       # LLM-based transaction categorizer
│   │   │   └── tabular_rag.py       # Text-to-SQL + semantic search
│   │   │
│   │   ├── db/
│   │   │   ├── models.py            # SQLAlchemy models
│   │   │   ├── session.py           # SQLite/SQLCipher connection
│   │   │   └── migrations/
│   │   │
│   │   └── utils/
│   │       ├── llm_client.py        # Abstraction: Ollama / OpenAI / Anthropic
│   │       └── math_engine.py       # Financial calculations (amortization, etc.)
│   │
│   ├── requirements.txt
│   └── pyproject.toml
│
├── docker-compose.yml           # Optional: containerized Ollama
├── Makefile                     # `make dev` starts both frontend + backend
└── README.md
```

---

## 3. Agent Architecture (LangGraph + Pydantic)

### 3.1 LangGraph Supervisor Pattern

```
                    ┌─────────────┐
          ┌────────►│   Router    │◄────────┐
          │         │  (Supervisor)│         │
          │         └──────┬──────┘         │
          │                │                │
    ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴──────┐
    │   Debt    │   │  Savings  │   │   Budget   │
    │  Analyzer │   │ Strategist│   │   Coach    │
    └─────┬─────┘   └─────┬─────┘   └─────┬──────┘
          │                │                │
          └────────┬───────┴────────┬───────┘
                   │                │
            ┌──────┴──────┐  ┌─────┴───────┐
            │   Payoff    │  │  Tabular    │
            │  Optimizer  │  │  RAG Tool   │
            └─────────────┘  └─────────────┘
```

### 3.2 Pydantic Structured Output Schemas

```python
# backend/app/agents/schemas.py

from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional

class DebtCategory(str, Enum):
    CREDIT_CARD = "credit_card"
    STUDENT_LOAN = "student_loan"
    MORTGAGE = "mortgage"
    AUTO_LOAN = "auto_loan"
    PERSONAL_LOAN = "personal_loan"
    MEDICAL = "medical"
    OTHER = "other"

class PayoffStrategy(str, Enum):
    AVALANCHE = "avalanche"       # Highest interest first
    SNOWBALL = "snowball"         # Smallest balance first
    HYBRID = "hybrid"            # Custom blend

class DebtItem(BaseModel):
    """A single debt obligation."""
    name: str = Field(..., description="Name/description of the debt")
    category: DebtCategory
    balance: float = Field(..., gt=0, description="Current outstanding balance")
    interest_rate: float = Field(..., ge=0, le=100, description="Annual interest rate %")
    minimum_payment: float = Field(..., ge=0)
    due_date: Optional[str] = None

    @field_validator("interest_rate")
    @classmethod
    def validate_rate(cls, v):
        if v > 50:
            # Self-correcting: flag suspicious rates
            raise ValueError(f"Interest rate {v}% seems unusually high. Please verify.")
        return v

class DebtAnalysis(BaseModel):
    """Structured output from the Debt Analyzer agent."""
    debts: list[DebtItem]
    total_debt: float
    weighted_avg_interest: float
    highest_priority_debt: str
    monthly_minimum_total: float
    debt_to_income_ratio: Optional[float] = None
    risk_level: str = Field(..., pattern="^(low|moderate|high|critical)$")
    summary: str

class BudgetCategory(BaseModel):
    category: str
    amount: float
    percentage_of_income: float
    recommendation: str  # "on_track", "reduce", "increase"
    suggested_amount: Optional[float] = None

class BudgetAdvice(BaseModel):
    """Structured output from the Budget Coach agent."""
    monthly_income: float
    total_expenses: float
    surplus_or_deficit: float
    categories: list[BudgetCategory]
    top_3_savings_opportunities: list[str]
    actionable_steps: list[str]
    fifty_thirty_twenty_analysis: dict  # needs vs wants vs savings

class SavingsStrategy(BaseModel):
    """Structured output from the Savings Strategist agent."""
    emergency_fund_target: float
    current_emergency_fund: float
    months_of_runway: float
    recommended_monthly_savings: float
    savings_vehicles: list[dict]  # e.g., [{"type": "HYSA", "reason": "..."}]
    milestone_timeline: list[dict]  # [{"goal": "3-mo emergency", "eta": "Aug 2026"}]
    strategy_narrative: str

class PayoffPlan(BaseModel):
    """Structured output from the Payoff Optimizer agent."""
    strategy: PayoffStrategy
    monthly_budget_for_debt: float
    payoff_order: list[dict]  # [{debt_name, months_to_payoff, total_interest_paid}]
    total_interest_saved_vs_minimum: float
    debt_free_date: str
    monthly_schedule: list[dict]  # First 12 months breakdown
    comparison: dict  # avalanche vs snowball side-by-side
```

### 3.3 Self-Correcting Agent Pattern

```python
# backend/app/agents/debt_analyzer.py

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import ValidationError
from .schemas import DebtAnalysis

MAX_RETRIES = 3

class DebtAnalyzerAgent:
    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=DebtAnalysis)

    async def analyze(self, user_data: dict, chat_history: list) -> DebtAnalysis:
        system_prompt = f"""You are a debt analysis expert. Analyze the user's
        financial data and produce a structured debt analysis.

        {self.parser.get_format_instructions()}

        Rules:
        - All monetary values in USD
        - Interest rates as percentages (e.g., 24.99 not 0.2499)
        - Risk levels: low (<20% DTI), moderate (20-35%), high (35-50%), critical (>50%)
        - Be conservative in estimates
        """

        messages = [
            SystemMessage(content=system_prompt),
            *chat_history,
            HumanMessage(content=f"Here is my financial data:\n{user_data}")
        ]

        # Self-correcting loop
        for attempt in range(MAX_RETRIES):
            try:
                response = await self.llm.ainvoke(messages)
                result = self.parser.parse(response.content)
                return result  # Pydantic validation passed
            except ValidationError as e:
                # Feed error back to LLM for self-correction
                error_msg = f"""Your previous output had validation errors:
                {str(e)}

                Please fix these issues and try again. Output ONLY valid JSON."""
                messages.append(HumanMessage(content=error_msg))
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                continue

        raise RuntimeError("Agent failed to produce valid output after retries")
```

### 3.4 LangGraph Orchestrator

```python
# backend/app/agents/graph.py

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated, Literal
from operator import add

class AgentState(TypedDict):
    messages: Annotated[list, add]
    user_financial_data: dict
    debt_analysis: dict | None
    budget_advice: dict | None
    savings_strategy: dict | None
    payoff_plan: dict | None
    current_agent: str
    needs_clarification: bool

def create_advisor_graph(llm, db_path: str):
    # Persistent checkpointing — survives server restart
    memory = SqliteSaver.from_conn_string(db_path)

    graph = StateGraph(AgentState)

    # Add agent nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("debt_analyzer", debt_analyzer_node)
    graph.add_node("savings_strategist", savings_strategist_node)
    graph.add_node("budget_coach", budget_coach_node)
    graph.add_node("payoff_optimizer", payoff_optimizer_node)
    graph.add_node("tabular_rag", tabular_rag_node)
    graph.add_node("clarify", clarification_node)

    # Supervisor routes to the right agent
    graph.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "debt_analyzer": "debt_analyzer",
            "savings_strategist": "savings_strategist",
            "budget_coach": "budget_coach",
            "payoff_optimizer": "payoff_optimizer",
            "clarify": "clarify",
            "end": END,
        }
    )

    # All agents can call tabular_rag as a tool, then return to supervisor
    for agent in ["debt_analyzer", "savings_strategist",
                   "budget_coach", "payoff_optimizer"]:
        graph.add_edge(agent, "supervisor")

    graph.add_edge("clarify", END)  # Ask user, wait for next turn
    graph.set_entry_point("supervisor")

    return graph.compile(checkpointer=memory)


def route_supervisor(state: AgentState) -> str:
    """Supervisor LLM decides which agent handles the query."""
    # This is where the supervisor uses the LLM to classify intent
    # Returns one of the agent names or "end"
    ...
```

---

## 4. Tabular RAG (Document → Queryable Data)

This is the bridge between uploaded bank statements/spreadsheets and the agents.

```python
# backend/app/ingestion/tabular_rag.py

import pandas as pd
from sqlalchemy import create_engine, text
from langchain_community.utilities import SQLDatabase

class TabularRAG:
    """
    1. User uploads CSV/XLSX/PDF bank statement
    2. Parser extracts → pandas DataFrame
    3. DataFrame loads into SQLite table
    4. Agents query via natural language → Text-to-SQL
    5. Results feed back into agent context
    """

    def __init__(self, db_path: str, llm):
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.llm = llm
        self.db = SQLDatabase(engine=self.engine)

    def ingest(self, df: pd.DataFrame, table_name: str):
        """Load a DataFrame into SQLite for querying."""
        df.to_sql(table_name, self.engine, if_exists="replace", index=False)

    async def query(self, natural_language_query: str) -> dict:
        """Convert natural language → SQL → results."""
        # Get schema context
        schema = self.db.get_table_info()

        prompt = f"""Given this database schema:
        {schema}

        Convert this question to SQL:
        {natural_language_query}

        Return ONLY the SQL query, nothing else."""

        response = await self.llm.ainvoke(prompt)
        sql = response.content.strip().strip("```sql").strip("```")

        # Execute with safety: read-only, parameterized
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            columns = result.keys()

        return {
            "sql": sql,
            "columns": list(columns),
            "rows": [dict(zip(columns, row)) for row in rows],
            "count": len(rows)
        }
```

---

## 5. FastAPI Backend

```python
# backend/app/main.py

from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .config import settings
from .security import verify_jwt, create_token
from .agents.graph import create_advisor_graph
from .ingestion.parser import parse_document
from .ingestion.tabular_rag import TabularRAG

app = FastAPI(title="Financial Advisor Agent Engine")

# SECURITY: Only allow localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{settings.FRONTEND_PORT}"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Parse financial document → store in local SQLite."""
    df = await parse_document(file)
    rag = TabularRAG(settings.DB_PATH, get_llm())
    rag.ingest(df, table_name=f"user_{file.filename.split('.')[0]}")
    return {"rows": len(df), "columns": list(df.columns)}

@app.post("/api/chat")
async def chat(request: ChatRequest, user=Depends(verify_jwt)):
    """Multi-turn conversation with the agent graph."""
    graph = create_advisor_graph(get_llm(), settings.DB_PATH)

    async def stream():
        async for event in graph.astream(
            {"messages": request.messages, "user_financial_data": request.context},
            config={"configurable": {"thread_id": request.session_id}}
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

@app.post("/api/analyze/snapshot")
async def full_snapshot(user=Depends(verify_jwt)):
    """Run all 4 agents and return a complete financial snapshot."""
    ...

@app.delete("/api/data")
async def nuke_data(user=Depends(verify_jwt)):
    """Delete all local user data. The 'forget me' button."""
    os.remove(settings.DB_PATH)
    return {"status": "all_data_deleted"}
```

---

## 6. React Frontend — Key Components

### 6.1 SSE Streaming Hook

```javascript
// frontend/src/hooks/useAgentStream.js

import { useState, useCallback } from 'react';

export function useAgentStream() {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeAgent, setActiveAgent] = useState(null);

  const sendMessage = useCallback(async (content, context = {}) => {
    setIsStreaming(true);

    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        messages: [...messages, { role: 'user', content }],
        context,
        session_id: sessionStorage.getItem('session_id'),
      }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(l => l.startsWith('data: '));

      for (const line of lines) {
        const event = JSON.parse(line.slice(6));
        if (event.current_agent) setActiveAgent(event.current_agent);
        if (event.messages) {
          setMessages(prev => [...prev, ...event.messages]);
        }
      }
    }

    setIsStreaming(false);
  }, [messages]);

  return { messages, sendMessage, isStreaming, activeAgent };
}
```

### 6.2 Dashboard Layout (High Level)

```
┌──────────────────────────────────────────────────────────┐
│  🔒 Your data never leaves this device    [Nuke Data 🗑️] │
├────────────────┬─────────────────────────────────────────┤
│                │                                         │
│  SIDEBAR       │   MAIN AREA                             │
│                │                                         │
│  📊 Dashboard  │   ┌─────────────┐  ┌─────────────────┐ │
│  💬 Chat       │   │ Debt Donut  │  │ Budget 50/30/20 │ │
│  📄 Upload     │   │   Chart     │  │    Bar Chart    │ │
│  ⚙️ Settings   │   └─────────────┘  └─────────────────┘ │
│                │                                         │
│  AGENTS        │   ┌──────────────────────────────────┐  │
│  ┌──────────┐  │   │  Payoff Timeline                 │  │
│  │🟢 Debt   │  │   │  ████████░░░░ 2027               │  │
│  │🟢 Budget │  │   │  ██████████░░ 2028               │  │
│  │🟡 Savings│  │   └──────────────────────────────────┘  │
│  │⚪ Payoff │  │                                         │
│  └──────────┘  │   ┌──────────────────────────────────┐  │
│                │   │  💬 Agent Chat                    │  │
│                │   │  ┌────────────────────────────┐   │  │
│                │   │  │ 🤖 Debt Analyzer:          │   │  │
│                │   │  │ Your highest priority is...│   │  │
│                │   │  └────────────────────────────┘   │  │
│                │   │  [Type your question...]   [Send] │  │
│                │   └──────────────────────────────────┘  │
└────────────────┴─────────────────────────────────────────┘
```

---

## 7. Tech Stack Summary

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | React 19 + Vite | Fast HMR, your standard stack |
| **Charts** | Recharts | React-native charting, lightweight |
| **Styling** | Tailwind CSS | Rapid prototyping for hackathon |
| **Backend** | FastAPI (Python 3.12) | Async, fast, Pydantic-native |
| **Agents** | LangGraph | Stateful multi-agent orchestration with checkpointing |
| **Structured Output** | Pydantic v2 | Self-correcting via validation errors fed back to LLM |
| **LLM Abstraction** | LangChain ChatModel | Swap Ollama ↔ OpenAI ↔ Anthropic with one env var |
| **Local LLM** | Ollama (llama3.1 8B) | Zero data leakage, runs on M1/M2 or decent GPU |
| **Database** | SQLite + SQLCipher | Encrypted at rest, single file, zero infra |
| **Tabular RAG** | Text-to-SQL via LangChain SQLDatabase | Natural language queries over uploaded spreadsheets |
| **Doc Parsing** | pandas + pdfplumber + openpyxl | CSV, XLSX, PDF bank statements |
| **Streaming** | SSE (Server-Sent Events) | Simpler than WebSockets, sufficient for agent streaming |

---

## 8. Hackathon Execution Timeline

### Phase 1: Foundation (2-3 hours)
```
□ Scaffold frontend: npm create vite@latest frontend -- --template react
□ Scaffold backend: FastAPI + SQLAlchemy + Pydantic models
□ Set up Ollama with llama3.1 (or configure API key)
□ Implement file upload → parse → SQLite pipeline
□ Get a basic "upload CSV, see data in table" flow working end-to-end
```

### Phase 2: Agent Engine (3-4 hours)
```
□ Build the 4 Pydantic output schemas (already drafted above)
□ Implement DebtAnalyzerAgent with self-correcting loop
□ Implement BudgetCoachAgent
□ Implement SavingsStrategistAgent
□ Implement PayoffOptimizerAgent
□ Wire up LangGraph supervisor with conditional routing
□ Test each agent individually with sample data
□ Add SSE streaming endpoint
```

### Phase 3: Frontend Dashboard (2-3 hours)
```
□ Build ChatInterface with SSE streaming
□ Build Dashboard with Recharts (debt donut, budget bars, payoff timeline)
□ Build FileUpload with drag-and-drop
□ Wire up useAgentStream hook
□ Add agent status indicators (which agent is "thinking")
□ Security banner + nuke data button
```

### Phase 4: Polish & Demo (1-2 hours)
```
□ Add sample financial data for demo
□ End-to-end test: upload → analyze → chat → visualize
□ Record a 3-min demo video or prepare live demo
□ Write README with setup instructions
```

---

## 9. Key Concepts Demonstrated

This project showcases all the following in a working app:

1. **Multi-Agent Orchestration** — LangGraph supervisor routing to specialist agents
2. **Structured Output** — Pydantic schemas enforced on LLM responses
3. **Self-Correcting Agents** — Validation errors fed back for retry
4. **Multi-Turn Conversation** — LangGraph checkpointer maintains state across turns
5. **Tabular RAG** — Natural language → SQL over user's financial data
6. **Streaming** — SSE-based real-time agent response streaming
7. **Live Dashboarding** — Charts update as agents produce structured analysis
8. **Security by Design** — Local-only, encrypted, no cloud exposure
9. **Document Ingestion** — PDF/CSV/XLSX → queryable structured data

---

## 10. Quick Start Commands

```bash
# Terminal 1: Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn langchain langgraph langchain-community \
            pydantic sqlalchemy pdfplumber openpyxl pandas
ollama pull llama3.1:8b  # If using local LLM
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev

# Terminal 3: Ollama (if using local LLM)
ollama serve
```

---

## 11. Sample Demo Script

For the hackathon demo, walk through this flow:

1. **"Meet your financial advisor"** — Show the security banner, explain local-only architecture
2. **Upload** — Drop in a sample bank statement CSV (pre-prepared with realistic data)
3. **Auto-analysis** — Watch as agents light up: Debt Analyzer → Budget Coach → Savings → Payoff
4. **Dashboard populates** — Charts animate in with analysis results
5. **Chat interaction** — Ask: "What's my biggest money leak?" → Budget Coach responds with structured data
6. **Follow-up** — Ask: "Should I use avalanche or snowball for my credit cards?" → Payoff Optimizer gives side-by-side comparison
7. **Nuke it** — Hit the delete button, show data is gone

---

## 12. Sample Test Data

Prepare a CSV like this for demo:

```csv
date,description,amount,type
2026-04-01,Paycheck,4500.00,income
2026-04-02,Rent,-1400.00,expense
2026-04-03,Grocery Store,-127.50,expense
2026-04-05,Netflix,-15.99,expense
2026-04-05,Credit Card Payment,-250.00,debt_payment
2026-04-07,Student Loan Payment,-350.00,debt_payment
2026-04-10,Restaurant,-68.00,expense
2026-04-12,Gas Station,-45.00,expense
2026-04-15,Paycheck,4500.00,income
2026-04-15,Electric Bill,-145.00,expense
2026-04-18,Amazon,-89.99,expense
2026-04-20,Uber Eats,-32.50,expense
2026-04-22,Gym Membership,-49.99,expense
2026-04-25,Car Insurance,-180.00,expense
```

And a debts summary:

```csv
name,type,balance,interest_rate,minimum_payment
Chase Sapphire,credit_card,4200.00,24.99,105.00
Student Loan,student_loan,28500.00,5.50,350.00
Car Loan,auto_loan,12000.00,6.99,280.00
Medical Bill,medical,2100.00,0.00,175.00
```
