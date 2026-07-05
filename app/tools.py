"""
tools.py
--------
These are the "hands" of the agent. Each function is a plain Python
function with a clear input/output. The agent (in agent.py) decides
WHEN to call which tool and WHY - that reasoning is what makes this
"agentic" rather than just a single LLM call.

Each tool is paired with a JSON schema (TOOL_DEFINITIONS) that we hand
to the Claude API so the model knows what tools exist and how to call them.
"""

from collections import defaultdict
from app.db import get_all_transactions, update_category


def get_spending_summary(month: str = None) -> dict:
    """
    Returns total spend per category, optionally filtered to a specific
    month (format 'YYYY-MM'). This is the tool the agent calls whenever
    the user asks something like "how much did I spend on food".
    """
    transactions = get_all_transactions()
    totals = defaultdict(float)
    total_spent = 0.0
    total_income = 0.0

    for t in transactions:
        if month and not t["date"].startswith(month):
            continue
        amount = t["amount"]
        category = t["category"] or "Uncategorized"
        if amount < 0:
            totals[category] += abs(amount)
            total_spent += abs(amount)
        else:
            total_income += amount

    return {
        "month": month or "all",
        "by_category": dict(totals),
        "total_spent": round(total_spent, 2),
        "total_income": round(total_income, 2),
        "net": round(total_income - total_spent, 2),
    }


def check_budget_limit(category: str, limit: float, month: str = None) -> dict:
    """
    Checks whether spend in a given category has crossed a limit.
    The agent calls this proactively for budgeting questions.
    """
    summary = get_spending_summary(month=month)
    spent = summary["by_category"].get(category, 0.0)
    return {
        "category": category,
        "limit": limit,
        "spent": spent,
        "remaining": round(limit - spent, 2),
        "over_budget": spent > limit,
    }


def detect_anomalies(threshold_pct: float = 50.0) -> list:
    """
    Flags transactions in a category whose amount is significantly higher
    than that category's average (e.g. a subscription that renewed at
    double its usual price). This is what makes the agent feel
    "autonomous" rather than reactive - it can surface things the user
    didn't explicitly ask about.
    """
    transactions = get_all_transactions()
    by_category = defaultdict(list)
    for t in transactions:
        if t["amount"] < 0:
            by_category[t["category"] or "Uncategorized"].append(t)

    anomalies = []
    for category, txns in by_category.items():
        if len(txns) < 2:
            continue
        amounts = [abs(t["amount"]) for t in txns]
        avg = sum(amounts) / len(amounts)
        for t in txns:
            amt = abs(t["amount"])
            if avg > 0 and (amt - avg) / avg * 100 >= threshold_pct:
                anomalies.append(
                    {
                        "date": t["date"],
                        "description": t["description"],
                        "amount": amt,
                        "category": category,
                        "category_average": round(avg, 2),
                        "pct_above_average": round((amt - avg) / avg * 100, 1),
                    }
                )
    return anomalies


def categorize_transaction(transaction_id: int, category: str) -> dict:
    """
    Lets the agent (or the LLM's own judgement) assign/correct a category
    for a specific transaction, e.g. for anything left 'Uncategorized'
    by the rule-based parser.
    """
    update_category(transaction_id, category)
    return {"transaction_id": transaction_id, "new_category": category, "status": "updated"}


def list_uncategorized() -> list:
    """Returns transactions the rule-based parser could not confidently label."""
    transactions = get_all_transactions()
    return [t for t in transactions if t["category"] == "Uncategorized"]


# ---------------------------------------------------------------------------
# Tool schemas passed to the Claude API so the model knows what it can call.
# https://docs.claude.com/en/docs/build-with-claude/tool-use
# ---------------------------------------------------------------------------
TOOL_DEFINITIONS = [
    {
        "name": "get_spending_summary",
        "description": "Get total spend per category, plus total income/spend/net, "
        "optionally filtered to one month. Use this whenever the user asks "
        "about spending, income, or wants an overview.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {
                    "type": "string",
                    "description": "Optional month filter in 'YYYY-MM' format.",
                }
            },
        },
    },
    {
        "name": "check_budget_limit",
        "description": "Check whether spend in a specific category has exceeded a given limit.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "limit": {"type": "number"},
                "month": {"type": "string", "description": "Optional 'YYYY-MM' filter."},
            },
            "required": ["category", "limit"],
        },
    },
    {
        "name": "detect_anomalies",
        "description": "Find transactions that are unusually high compared to the "
        "average for their category (e.g. a subscription price hike). "
        "Use this proactively when the user asks if anything looks off, "
        "or periodically to surface issues the user didn't ask about.",
        "input_schema": {
            "type": "object",
            "properties": {
                "threshold_pct": {
                    "type": "number",
                    "description": "Percent above category average to flag. Default 50.",
                }
            },
        },
    },
    {
        "name": "categorize_transaction",
        "description": "Assign or correct the category of a specific transaction by its id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "integer"},
                "category": {"type": "string"},
            },
            "required": ["transaction_id", "category"],
        },
    },
    {
        "name": "list_uncategorized",
        "description": "List all transactions that don't yet have a confident category.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

# Maps tool name -> actual Python function, so the agent loop can dispatch calls.
TOOL_FUNCTIONS = {
    "get_spending_summary": get_spending_summary,
    "check_budget_limit": check_budget_limit,
    "detect_anomalies": detect_anomalies,
    "categorize_transaction": categorize_transaction,
    "list_uncategorized": list_uncategorized,
}
