# meridian-capital

**Meridian** — a local-first, multi-agent personal finance advisor.
Streamlit hackathon demo, ported from a Claude Design HTML/React prototype.

A supervisor agent decomposes your questions and routes them to four
specialists (Debt Analyzer, Savings Strategy, Budget Advisor, Payoff
Optimizer), all reasoning over a private document vault on your machine.
Nothing leaves the device.

## Run

```sh
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`.

## Layout

```
meridian-capital/
├── streamlit_app.py     shell — sidebar nav, view router
├── theme.py             color tokens + CSS injection (Geist + Newsreader)
├── data.py              mock persona, agent metadata, seeded chat trace
│
├── views/               one Streamlit view per file
│   ├── dashboard.py     hero stats, net-worth chart, agent insights
│   ├── documents.py     upload, ingestion pipeline, sources table
│   ├── debt.py          balance trajectory, interest mix, debts table
│   ├── savings.py       growth chart, surplus allocation, goals
│   ├── budget.py        category bars vs targets, spending trend
│   ├── payoff.py        snowball / avalanche / min comparison
│   ├── settings.py      vault status, security checklist, uploads
│   └── chat.py          advisor chat with orchestration trace
│
├── agents/              agent layer (stubs today — see docs/AGENTS.md)
│   ├── supervisor.py    decompose · route · synthesize
│   ├── debt.py · savings.py · budget.py · payoff.py
│   ├── tools.py         query_*, rag_retrieve, simulate_*, project_*
│   └── types.py         Trace / Step / AgentMessage TypedDicts
│
├── sample_data/         seed CSVs to drag into the Documents tab
│   ├── chase_checking_apr2026.csv      (142 rows)
│   ├── capital_one_apr2026.csv         (41 rows)
│   ├── honda_auto_loan.csv             (24 rows · amortization)
│   ├── schwab_brokerage_q1.csv         (18 rows · holdings + activity)
│   ├── wells_mortgage_q1.csv           (3 rows · statement summary)
│   └── sofi_student_loan_apr.csv       (1 row · loan statement)
│
├── assets/              logos, screenshots, gif captures
├── docs/                project documentation (read these first)
│   ├── ARCHITECTURE.md  system overview, local-first wedge, tabular RAG
│   ├── AGENTS.md        each agent's role, tools, trace schema
│   ├── DEMO.md          5–7 min hackathon-judge walkthrough
│   ├── DATA_MODEL.md    PERSONA + CHAT_SEED schemas
│   └── COPY.md          canonical empty-state and help copy
│
└── requirements.txt
```

## Demo path

1. **Documents** → drop the six files from `sample_data/`. Watch the
   5-step pipeline animate (Parse → Normalize → Redact → Embed → Index).
2. **Dashboard** → net worth, agent insights at a glance.
3. **Advisor chat** → ask *"I just got a $3,200 bonus. What should I do
   with it?"* — open the **"How I answered this"** trace under the reply
   to see supervisor → debt → payoff → savings → synthesizer with tool
   calls.
4. **Payoff** → toggle Snowball / Avalanche / Min — chart re-projects.
5. **Settings** → local-first vault status + security checklist.

The orchestration trace under chat replies is the hackathon-judge moment —
it makes the multi-agent architecture *visible* instead of hidden behind
a polished output. See `docs/DEMO.md` for the full script.

## What's real today vs. what's mocked

The **UI**, **document upload pipeline**, **trace rendering**, and the
**sample CSVs** are all real. The **agent layer** is stubbed (returns
canonical fixtures from `data.py::CHAT_SEED`). The mocks live behind the
same interfaces real implementations will satisfy — see
`docs/ARCHITECTURE.md#path-to-a-real-implementation`.
