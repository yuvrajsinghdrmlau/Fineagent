# FinAgent — Agentic AI Finance Tracker

FinAgent is a personal finance tracker built around an **autonomous LLM agent**,
not just a chatbot wrapper. Instead of hardcoding what to compute, the agent
decides for itself which tools to call, in what order, and how many steps it
needs to answer a question — chaining tool calls until it has enough
information to respond.

## Why this is "agentic" and not just a GenAI wrapper

A typical GenAI finance demo pipes your data into a prompt and asks an LLM to
"analyze" it in one shot. FinAgent instead gives the model **tools** and lets
it plan:

- Ask *"Can I afford a ₹5,000 dinner this month?"* → the agent decides on its
  own to call `get_spending_summary`, then `check_budget_limit`, reasons over
  both results, and only then answers — you can watch this reasoning happen
  turn by turn in the terminal.
- The agent also runs **anomaly detection** proactively (e.g. catching a
  subscription that silently doubled in price) without being explicitly asked.

## Architecture  

```
┌─────────────┐      ┌──────────────┐      ┌───────────────────┐
│  Streamlit  │      │   FastAPI     │      │   Claude API       │
│  / FastAPI  │─────▶│   backend     │─────▶│   (tool-use loop)  │
│  frontend   │      │  (main.py)    │      │   agent.py          │
└─────────────┘      └──────┬───────┘      └─────────┬──────────┘
                             │                        │ calls tools
                             ▼                        ▼
                      ┌─────────────┐          ┌─────────────┐
                      │  SQLite DB  │◀─────────│  tools.py    │
                      │  (db.py)    │          │ (summary,    │
                      └─────────────┘          │  budget,     │
                                                │  anomaly,    │
                                                │  categorize) │
                                                └─────────────┘
```

**Agent loop (perceive → plan → act → observe → respond):**
1. User asks a question.
2. Claude decides whether it needs data, and if so, which tool to call.
3. The tool runs in Python against the SQLite database; the result is fed
   back to Claude.
4. Claude either calls another tool (multi-step reasoning) or gives a
   final answer.

This loop is implemented from scratch in [`app/agent.py`](app/agent.py) using
the Claude API's native tool-use feature — no heavyweight agent framework
required to understand the core mechanics.

## Features

- 📄 CSV statement parsing with rule-based pre-categorization
- 🧠 LLM agent that autonomously selects and chains tool calls
- 📊 Spending summaries by category, month-over-month
- 💸 Budget limit checks
- ⚠️ Automatic anomaly detection (e.g. price hikes, unusual spend spikes)
- 🖥️ Streamlit dashboard + FastAPI REST backend

## Tech stack

Python · Anthropic Claude API (tool use) · FastAPI · Streamlit · SQLite · Pandas

## Getting started

```bash
git clone https://github.com/<your-username>/finagent.git
cd finagent
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # then add your ANTHROPIC_API_KEY
```

Load environment variables (Linux/Mac):
```bash
export $(cat .env | xargs)
```

### Run the dashboard
```bash
streamlit run streamlit_app.py
```

### Or run the API
```bash
uvicorn main:app --reload
# visit http://localhost:8000/docs
```

### Or test the agent directly in the terminal
```bash
python -m app.agent
```

## Example questions to try

- "How much did I spend on food this month?"
- "Am I over budget on groceries if my limit is ₹5000?"
- "Did anything unusual happen with my subscriptions?"
- "What's my net savings so far?"

## Project structure

```
finagent/
├── app/
│   ├── agent.py       # Core agent loop (Claude tool-use)
│   ├── tools.py        # Tools the agent can call + their schemas
│   ├── db.py            # SQLite persistence layer
│   └── parser.py         # CSV statement parsing + rule-based categorization
├── sample_data/
│   └── transactions.csv  # Sample statement to try immediately
├── main.py                # FastAPI backend
├── streamlit_app.py        # Streamlit dashboard
└── requirements.txt
```

## Roadmap / possible extensions

- Multi-agent version (Categorizer, Analyst, Advisor agents) using LangGraph
- RAG over historical statements for "why did I overspend in March"-style questions
- Live stock/index data tool to compare savings vs. market performance
- Recurring bill detection and predictive cash-flow alerts  

## License

MIT
