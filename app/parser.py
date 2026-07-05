"""
parser.py
---------
Reads a bank/UPI statement CSV and loads it into the database.
A simple keyword-based categorizer runs first (fast, free, no LLM call needed
for obvious cases). Anything it can't confidently label is left as
"Uncategorized" so the agent can categorize it later using the LLM tool.
"""

import csv
from pathlib import Path
from app.db import insert_transaction, clear_all

# Simple keyword -> category rules.
# This is intentionally basic - the LLM agent handles the harder cases.
CATEGORY_RULES = {
    "Food & Dining": ["swiggy", "zomato", "restaurant", "cafe"],
    "Rent": ["rent"],
    "Subscriptions": ["netflix", "spotify", "prime", "hotstar"],
    "Transport": ["uber", "ola", "petrol", "fuel"],
    "Groceries": ["bigbasket", "grocery", "grofers", "dmart"],
    "Utilities": ["electricity", "bses", "recharge", "jio", "airtel", "wifi", "broadband"],
    "Shopping": ["amazon", "flipkart", "myntra"],
    "Investments": ["mutual fund", "sip", "zerodha", "groww", "stock broker"],
    "Health & Fitness": ["gym", "cultfit", "pharmacy", "hospital"],
    "Entertainment": ["movie", "pvr", "bookmyshow"],
    "Credit Card Payment": ["credit card bill"],
    "Income": ["salary", "salary credit", "freelance income", "refund"],
}


def rule_based_category(description: str) -> str:
    desc_lower = description.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(kw in desc_lower for kw in keywords):
            return category
    return "Uncategorized"


def load_statement(csv_path: str, reset: bool = True):
    """
    Parse a CSV with columns: date, description, amount
    and insert rows into the database.
    """
    if reset:
        clear_all()

    csv_path = Path(csv_path)
    count = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row["date"].strip()
            description = row["description"].strip()
            amount = float(row["amount"])
            category = rule_based_category(description)
            insert_transaction(date, description, amount, category)
            count += 1

    return count


if __name__ == "__main__":
    # Quick manual test: python -m app.parser
    from app.db import init_db

    init_db()
    n = load_statement("sample_data/transactions.csv")
    print(f"Loaded {n} transactions.")
