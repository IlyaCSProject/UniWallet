# Shared database helper. Reads transactions from the SQLite DB used by
# the Expense Log, and reshapes them so the Dashboard and Prediction pages
# can use the same columns they used with sample data.

import os
import sqlite3
import pandas as pd

# Path to the SQLite database (sits next to app.py)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_THIS_DIR)
DB_PATH   = os.path.join(_ROOT_DIR, "uniwallet_expenses.db")


def get_expenses() -> pd.DataFrame:
    """Return all logged transactions with columns:
    date, description, category, currency, amount_original, amount (CHF).
    Raises if the DB is missing or empty so callers can fall back to sample data.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM expenses ORDER BY date ASC, id ASC", conn
        )

    if df.empty:
        raise ValueError("Database is empty")

    df["date"] = pd.to_datetime(df["date"])

    # Old CHF rows didn't store amount_chf separately, fall back to amount
    df["amount_chf"] = df["amount_chf"].fillna(df["amount"])

    # Rename to match what the Dashboard / Prediction pages expect
    df = df.rename(columns={
        "amount":     "amount_original",
        "amount_chf": "amount",
    })

    return df[["date", "description", "category", "currency",
               "amount_original", "amount"]].copy()
