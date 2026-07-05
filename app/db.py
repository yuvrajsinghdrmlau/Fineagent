"""
db.py
-----
Very small SQLite wrapper for storing transactions.
Kept deliberately simple (no ORM) so it's easy to read and explain in an interview.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "finagent.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the transactions table if it doesn't already exist."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def insert_transaction(date: str, description: str, amount: float, category: str = None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO transactions (date, description, amount, category) VALUES (?, ?, ?, ?)",
        (date, description, amount, category),
    )
    conn.commit()
    conn.close()


def update_category(transaction_id: int, category: str):
    conn = get_connection()
    conn.execute(
        "UPDATE transactions SET category = ? WHERE id = ?", (category, transaction_id)
    )
    conn.commit()
    conn.close()


def get_all_transactions():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM transactions ORDER BY date").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def clear_all():
    """Useful when re-importing a fresh statement during testing."""
    conn = get_connection()
    conn.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
