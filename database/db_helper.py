# =============================================================================
# UniWallet — Shared Database Helper
# University of St. Gallen  ·  Fundamentals & Methods of CS  ·  Spring 2026
# =============================================================================
#
# This module is imported by all pages that need to read transaction data.
# It connects to the SAME SQLite database that the Expense Log writes to,
# and returns a DataFrame in the format the Dashboard and Prediction pages
# expect (with columns: date, description, category, currency,
# amount_original, amount).
#
# The Expense Log itself does NOT use this module — it has its own copy of
# the database functions because it also needs to insert/update/delete rows.
# =============================================================================

import os
import sqlite3
import pandas as pd

# ── Path to the SQLite database ───────────────────────────────────────────────
# The database lives at the project root (next to app.py). We compute the
# absolute path so this works regardless of where the script is run from.
_THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR  = os.path.dirname(_THIS_DIR)
DB_PATH    = os.path.join(_ROOT_DIR, "uniwallet_expenses.db")


def get_expenses() -> pd.DataFrame:
    """
    Read all transactions from the database and return them as a DataFrame
    in the format that the Dashboard and Prediction pages expect.

    The database schema (written by the Expense Log) has columns:
        id, date, description, category, currency, amount, amount_chf, note

    The Dashboard and Prediction pages expect:
        date, description, category, currency, amount_original, amount
    where 'amount_original' is the value in its original currency,
    and 'amount' is the value already converted to CHF.

    Raises FileNotFoundError if the database does not exist yet.
    Raises ValueError if the database has no entries yet.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    # Open a connection and read all rows ordered by date (oldest first,
    # so cumulative calculations work correctly)
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM expenses ORDER BY date ASC, id ASC", conn
        )

    # If the table is empty, signal that to the caller
    if df.empty:
        raise ValueError("Database is empty — no expenses logged yet")

    # Convert the date string column into actual datetime objects
    df["date"] = pd.to_datetime(df["date"])

    # If amount_chf is NULL (e.g. a CHF row from before the migration),
    # use the original amount as a fallback
    df["amount_chf"] = df["amount_chf"].fillna(df["amount"])

    # Rename columns so the Dashboard and Prediction pages can use them:
    # - 'amount'      column already contains the original-currency amount
    # - 'amount_chf'  column contains the CHF-converted amount
    # We rename them to match the expected names.
    df = df.rename(columns={
        "amount":     "amount_original",
        "amount_chf": "amount",
    })

    # Return only the columns the other pages need (drop id and note)
    return df[["date", "description", "category", "currency",
               "amount_original", "amount"]].copy()
