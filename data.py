"""Mock persona, agent metadata, and seeded chat — ported from the design's data.js."""

PERSONA = {
    "name": "Maya Patel",
    "initials": "MP",
    "net_worth": 184320,
    "net_worth_delta": 4280,
    "net_worth_series": [165000, 168200, 167800, 170400, 173000, 172500,
                         175800, 177200, 179400, 180900, 182600, 184320],
    "cash_flow": 2840,
    "cash_flow_delta": -180,
    "monthly_income": 9450,
    "monthly_expenses": 6610,
    "debts": [
        {"name": "Mortgage — 30yr fixed", "lender": "Wells Fargo", "balance": 312400, "rate": 5.875, "min": 2140, "type": "Mortgage", "risk": "low"},
        {"name": "Sapphire Preferred", "lender": "Chase", "balance": 4820, "rate": 22.49, "min": 145, "type": "Credit Card", "risk": "high"},
        {"name": "Quicksilver", "lender": "Capital One", "balance": 1980, "rate": 19.99, "min": 60, "type": "Credit Card", "risk": "high"},
        {"name": "Auto loan — Civic", "lender": "Honda Financial", "balance": 12640, "rate": 6.49, "min": 312, "type": "Auto", "risk": "medium"},
        {"name": "Grad school refi", "lender": "SoFi", "balance": 18420, "rate": 4.85, "min": 218, "type": "Student", "risk": "low"},
    ],
    "savings": [
        {"name": "Emergency fund", "balance": 9200, "target": 18000, "monthly": 400, "eta": "Mar 2028", "category": "Safety"},
        {"name": "House — kitchen reno", "balance": 6800, "target": 25000, "monthly": 600, "eta": "Aug 2029", "category": "Home"},
        {"name": "Vacation — Japan '26", "balance": 2400, "target": 5500, "monthly": 350, "eta": "Dec 2026", "category": "Lifestyle"},
        {"name": "Roth IRA '26", "balance": 3850, "target": 7000, "monthly": 583, "eta": "Dec 2026", "category": "Retirement"},
    ],
    "budget": [
        {"cat": "Housing", "spent": 2410, "budget": 2400},
        {"cat": "Groceries", "spent": 612, "budget": 700},
        {"cat": "Dining out", "spent": 486, "budget": 350},
        {"cat": "Transport", "spent": 312, "budget": 400},
        {"cat": "Subscriptions", "spent": 184, "budget": 150},
        {"cat": "Health", "spent": 220, "budget": 250},
        {"cat": "Shopping", "spent": 540, "budget": 400},
        {"cat": "Travel", "spent": 0, "budget": 200},
    ],
    "transactions": [
        {"date": "May 8", "merchant": "Trader Joe's", "cat": "Groceries", "amount": -84.20, "source": "Chase Checking"},
        {"date": "May 8", "merchant": "Lyft", "cat": "Transport", "amount": -12.40, "source": "Chase Checking"},
        {"date": "May 7", "merchant": "Direct Deposit — Acme Corp", "cat": "Income", "amount": 4725.00, "source": "Chase Checking"},
        {"date": "May 6", "merchant": "Spotify", "cat": "Subscriptions", "amount": -16.99, "source": "Capital One"},
        {"date": "May 6", "merchant": "Whole Foods", "cat": "Groceries", "amount": -52.10, "source": "Chase Checking"},
        {"date": "May 5", "merchant": "Shell", "cat": "Transport", "amount": -48.00, "source": "Capital One"},
        {"date": "May 5", "merchant": "Bartaco", "cat": "Dining out", "amount": -68.30, "source": "Chase Sapphire"},
        {"date": "May 4", "merchant": "Mortgage — Wells Fargo", "cat": "Housing", "amount": -2410.00, "source": "Chase Checking"},
    ],
    "documents": [
        {"name": "chase_checking_apr2026.csv", "size": "84 KB", "added": "May 8", "status": "ready", "rows": 142, "source": "Chase"},
        {"name": "capital_one_apr2026.pdf", "size": "240 KB", "added": "May 8", "status": "ready", "rows": 41, "source": "Capital One"},
        {"name": "wells_mortgage_q1.pdf", "size": "1.2 MB", "added": "May 7", "status": "ready", "rows": 3, "source": "Wells Fargo"},
        {"name": "sofi_student_loan_apr.pdf", "size": "180 KB", "added": "May 7", "status": "embedding", "rows": 1, "source": "SoFi"},
        {"name": "honda_auto_loan.csv", "size": "12 KB", "added": "May 6", "status": "ready", "rows": 24, "source": "Honda Financial"},
        {"name": "schwab_brokerage_q1.pdf", "size": "640 KB", "added": "May 4", "status": "ready", "rows": 18, "source": "Schwab"},
    ],
}

AGENT_META = {
    "supervisor": {"label": "Supervisor", "color": "#4A3B6B"},
    "debt":       {"label": "Debt Analyzer", "color": "#9E3A37"},
    "savings":    {"label": "Savings Strategy", "color": "#1E6B52"},
    "budget":     {"label": "Budget Advisor", "color": "#B27A1E"},
    "payoff":     {"label": "Payoff Optimizer", "color": "#2C4F7C"},
}

# Seeded chat — the $3,200 bonus scenario from the design
CHAT_SEED = [
    {"role": "user", "text": "I just got a $3,200 bonus. What should I do with it?"},
    {"role": "supervisor", "routing": ["debt", "savings", "payoff"],
     "text": "Routing to Debt Analyzer, Payoff Optimizer, and Savings Strategy."},
    {
        "role": "agent", "agent": "payoff",
        "text": "Pay $3,200 toward the **Sapphire Preferred** card (22.49% APR). That's the highest-rate balance you carry and the avalanche move saves you about **$612 in interest** over the next 18 months versus splitting the bonus.",
        "structured": {"kind": "recommend-payoff", "target": "Sapphire Preferred",
                       "amount": 3200, "interest_saved": 612},
        "trace": {
            "total_ms": 1820, "tool_count": 6,
            "steps": [
                {"kind": "supervisor", "title": "Decomposed into 3 sub-questions", "ms": 380,
                 "details": [
                     "Which debt yields the highest guaranteed return?",
                     "Is the emergency fund adequate for full payoff?",
                     "What's the long-run interest delta?",
                 ],
                 "routes": ["debt", "savings", "payoff"]},
                {"kind": "agent", "agent": "debt", "ms": 540,
                 "tools": [
                     {"name": "query_debt_table", "args": 'filter: "active", sort: "apr desc"', "result": "3 rows"},
                     {"name": "compute_apr_weighted_risk", "args": "debts", "result": "22.49% top APR"},
                 ],
                 "conclusion": "Sapphire Preferred is the highest-yield payoff target."},
                {"kind": "agent", "agent": "payoff", "ms": 620,
                 "tools": [
                     {"name": "rag_retrieve", "args": '"chase sapphire statement", k=5', "result": "rows 12, 47, 89, 104, 211"},
                     {"name": "simulate_avalanche", "args": "extra: $3,200, horizon: 18mo", "result": "−$612 interest"},
                 ],
                 "conclusion": "Avalanche move saves $612 vs split."},
                {"kind": "agent", "agent": "savings", "ms": 280,
                 "tools": [
                     {"name": "query_savings_goals", "args": 'filter: "emergency"', "result": "1 row · 51% of target"},
                 ],
                 "conclusion": "Emergency fund at 51% — flag for synthesis."},
                {"kind": "synth", "ms": 180,
                 "summary": "Merged 3 agent outputs · prioritized by certainty · flagged emergency-fund tradeoff for follow-up"},
            ],
        },
    },
    {
        "role": "agent", "agent": "savings",
        "text": "Counter-take: your **emergency fund is at 51%** of your 6-month target. If job stability is a concern, a 70/30 split (debt/emergency) keeps the avalanche logic mostly intact while strengthening your runway.",
        "trace": {
            "total_ms": 740, "tool_count": 3,
            "steps": [
                {"kind": "agent", "agent": "savings", "ms": 540,
                 "tools": [
                     {"name": "query_savings_goals", "args": 'filter: "emergency"', "result": "balance: $7,200 / $14,000"},
                     {"name": "rag_retrieve", "args": '"monthly fixed expenses 6mo"', "result": "rows 4, 18, 31"},
                     {"name": "project_runway", "args": "balance: 7200, burn: 4380/mo", "result": "1.6mo runway"},
                 ],
                 "conclusion": "Runway too thin for full payoff. Recommend 70/30 split."},
            ],
        },
    },
    {
        "role": "agent", "agent": "supervisor",
        "text": "**Synthesis** — both are reasonable. Highest expected value is full payoff to Sapphire if your role feels stable. Tap **Apply** to schedule, or ask a follow-up.",
        "actions": ["Apply payoff plan", "Split 70/30 instead", "What if I lose my job?"],
    },
]

# Pre-canned response for follow-up questions in the chat (budget+savings scenario)
FOLLOWUP_RESPONSE = [
    {"role": "supervisor", "routing": ["budget", "savings"],
     "text": "Routing to Budget Advisor and Savings Strategy."},
    {
        "role": "agent", "agent": "budget",
        "text": "You're **$136 over** in dining out and **$140 over** on shopping this month. Pulling those back to budget would free up about **$276** for goals.",
        "trace": {
            "total_ms": 980, "tool_count": 4,
            "steps": [
                {"kind": "supervisor", "title": "Decomposed into 2 sub-questions", "ms": 220,
                 "details": ["Where is spending exceeding budget?",
                             "How much can be redirected without lifestyle impact?"],
                 "routes": ["budget", "savings"]},
                {"kind": "agent", "agent": "budget", "ms": 480,
                 "tools": [
                     {"name": "query_transactions", "args": 'month: "May 2026"', "result": "127 rows"},
                     {"name": "compare_to_budget", "args": "by category", "result": "2 categories over"},
                     {"name": "rag_retrieve", "args": '"recurring discretionary"', "result": "rows 18, 44, 61"},
                 ],
                 "conclusion": "Dining +$136, Shopping +$140 — both discretionary."},
                {"kind": "agent", "agent": "savings", "ms": 200,
                 "tools": [{"name": "project_goal_eta", "args": "extra: $276/mo", "result": "−2mo to kitchen reno"}],
                 "conclusion": "Redirecting $276 cuts kitchen ETA by 2 months."},
                {"kind": "synth", "ms": 80,
                 "summary": "Merged 2 outputs · single recommendation · high confidence"},
            ],
        },
    },
    {
        "role": "agent", "agent": "supervisor",
        "text": "**Synthesis** — redirect that surplus to the kitchen-reno fund to cut its ETA by 2 months.",
        "actions": ["Apply", "Show alternatives"],
    },
]
