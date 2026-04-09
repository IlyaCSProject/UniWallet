# =============================================================================
# UniWallet — Expense Log
# University of St. Gallen  ·  Fundamentals & Methods of CS  ·  Spring 2026
# =============================================================================
# HOW TO RUN:
#   pip install streamlit plotly pandas numpy
#   streamlit run log_exp_alex.py
# =============================================================================

import sqlite3
import os
from datetime import datetime, date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="UniWallet — Expense Log", page_icon="W", layout="wide")

# ── COLOUR PALETTE ────────────────────────────────────────────────────────────
GREEN_DARK   = "#1A5C38"
GREEN_MID    = "#2A8A56"
GREEN_LIGHT  = "#4DB87A"
EUR_COLOR    = "#3B82F6"
CHART_COLORS = ["#1A5C38", "#2A8A56", "#4DB87A", "#7FCF9F", "#B2E4C8", "#D5F0E2"]

# ── DATABASE ──────────────────────────────────────────────────────────────────
DB_PATH = "uniwallet_expenses.db"

def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)

def init_db():
    """Create the expenses table if it does not exist yet."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT    NOT NULL,
                description TEXT    NOT NULL,
                category    TEXT    NOT NULL,
                currency    TEXT    NOT NULL DEFAULT 'CHF',
                amount      REAL    NOT NULL,
                note        TEXT
            )
        """)
        conn.commit()

init_db()

# ── HELPERS ───────────────────────────────────────────────────────────────────
CATEGORIES = [
    "Food & Drinks",
    "Transport",
    "Entertainment",
    "Shopping",
    "Education",
    "Utilities",
    "Income",
    "Other",
]

CURRENCIES = ["CHF", "EUR", "USD", "GBP", "JPY", "SEK", "CAD", "AUD"]

def load_expenses() -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM expenses ORDER BY date DESC, id DESC", conn
        )
    if df.empty:
        return pd.DataFrame(columns=["id", "date", "description", "category",
                                     "currency", "amount", "note"])
    df["date"] = pd.to_datetime(df["date"])
    return df

def insert_expense(date_val: date, description: str, category: str,
                   currency: str, amount: float, note: str):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO expenses (date, description, category, currency, amount, note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (date_val.strftime("%Y-%m-%d"), description, category,
             currency, amount, note or ""),
        )
        conn.commit()

def delete_expense(expense_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()

def update_expense(expense_id: int, date_val: date, description: str,
                   category: str, currency: str, amount: float, note: str):
    with get_connection() as conn:
        conn.execute(
            """UPDATE expenses
               SET date=?, description=?, category=?, currency=?, amount=?, note=?
               WHERE id=?""",
            (date_val.strftime("%Y-%m-%d"), description, category,
             currency, amount, note or "", expense_id),
        )
        conn.commit()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: #FFFFFF !important;
    color: #1C2B2B;
}

/* ── KPI cards ── */
.kpi-card {
    background: #FFFFFF;
    border: 1.5px solid #D1E7D9;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(26,92,56,.07);
    transition: box-shadow .2s, transform .2s;
    min-height: 104px;
    display: flex; flex-direction: column; justify-content: center;
}
.kpi-card:hover { box-shadow: 0 6px 18px rgba(26,92,56,.13); transform: translateY(-2px); }
.kpi-label { font-size: .7rem; font-weight: 600; text-transform: uppercase;
             letter-spacing: .08em; color: #5A6B6B; margin-bottom: 6px; }
.kpi-value { font-size: 1.65rem; font-weight: 700; line-height: 1.1; }
.kpi-sub   { font-size: .72rem; color: #5A6B6B; margin-top: 5px; }
.pos  { color: #1A5C38; }
.neg  { color: #4A5568; }
.blue { color: #3B82F6; }

/* ── Section headers ── */
.sec-header {
    font-size: 1rem; font-weight: 600; color: #1C2B2B;
    border-left: 4px solid #1A5C38; padding-left: 12px;
    margin-top: 2rem; margin-bottom: .75rem;
}

/* ── Page header ── */
.page-header {
    background: linear-gradient(120deg, #1A5C38 0%, #2A8A56 100%);
    border-radius: 14px; padding: 28px 36px; margin-bottom: 1.5rem;
}
.page-header h1 { font-size: 1.7rem; font-weight: 700; margin: 0; color: white; }
.page-header p  { margin: 6px 0 0; font-size: .88rem; opacity: .8; color: white; }

/* ── Add expense form card ── */
.form-card {
    background: #F0FAF4;
    border: 1.5px solid #D1E7D9;
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 1.5rem;
}

/* ── Toast-style success / error ── */
.toast-ok  { background:#D1FAE5; border:1px solid #6EE7B7; border-radius:10px;
             padding:12px 18px; color:#065F46; font-size:.85rem; font-weight:500; }
.toast-err { background:#FEE2E2; border:1px solid #FCA5A5; border-radius:10px;
             padding:12px 18px; color:#991B1B; font-size:.85rem; font-weight:500; }

/* ── Category pill ── */
.cat-pill {
    display:inline-block; font-size:.68rem; font-weight:600; border-radius:20px;
    padding:2px 10px; background:#E8F5EE; color:#1A5C38;
    border:1px solid #B2DEC7; white-space:nowrap;
}
.cat-pill-income { background:#DBEAFE; color:#1D4ED8; border:1px solid #93C5FD; }

/* ── Table row stripe ── */
.log-table-wrap {
    background:white; border:1.5px solid #D1E7D9; border-radius:12px;
    overflow:hidden;
}

/* ── Widget accent → green ── */
[data-testid="stSlider"] [role="slider"] { background: #1A5C38 !important; border-color: #1A5C38 !important; }

/* Multiselect selected tags */
[data-baseweb="tag"] { background-color: #E8F5EE !important; color: #1A5C38 !important;
                       border: 1px solid #B2DEC7 !important; }
[data-baseweb="tag"] span { color: #1A5C38 !important; }
[data-baseweb="tag"] button path { fill: #1A5C38 !important; }

/* Selectbox */
[data-baseweb="select"] > div { background-color: white !important; }
[data-baseweb="select"] [data-baseweb="select-container"] div,
[data-baseweb="select"] span,
[data-baseweb="select"] input,
[data-testid="stSelectbox"] div,
[data-testid="stSelectbox"] span { color: #1C2B2B !important; }
[data-baseweb="popover"],
[data-baseweb="menu"]   { background-color: white !important; border: 1px solid #D1E7D9 !important; }
[data-baseweb="option"] { background-color: white !important; color: #1C2B2B !important; }
[data-baseweb="option"]:hover { background-color: #E8F5EE !important; }

/* Dataframe */
[data-testid="stDataFrame"],
.stDataFrame { background-color: white !important; border: 1px solid #D1E7D9 !important; border-radius: 10px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background-color: #F5FBF7 !important; border-right: 1px solid #D1E7D9; }
[data-testid="stSidebarNav"] { display: none !important; }


/* ── Force ALL sidebar text to be dark and readable ── */
[data-testid="stSidebar"] * {
    color: #1C2B2B !important;
}
[data-testid="stSidebar"] a { color: #1A5C38 !important; text-decoration: none !important; }
[data-testid="stSidebar"] a:hover { background-color: #E0F0E8 !important; }
[data-testid="stSidebar"] .sb-logo-text .sb-sub { color: #5A6B6B !important; }
[data-testid="stSidebar"] small { color: #5A6B6B !important; }

/* ── Info / warning bars — dark text ── */
[data-testid="stAlert"] p,
[data-testid="stAlert"] span,
div[data-baseweb="notification"] div { color: #1C2B2B !important; }

.sb-logo { display:flex; align-items:center; gap:12px; padding-bottom:18px;
           border-bottom:1px solid #D1E7D9; margin-bottom:6px; }
.sb-logo-text .sb-name { font-size:1.15rem; font-weight:700; color:#1A5C38; line-height:1.2; }
.sb-logo-text .sb-sub  { font-size:.68rem; color:#5A6B6B; letter-spacing:.03em; }

.nav-section { margin: 12px 0 4px; }
.nav-label   { font-size:.65rem; font-weight:600; text-transform:uppercase;
               letter-spacing:.09em; color:#8A9A9A; padding:0 4px; margin-bottom:6px; }
.nav-item {
    display:flex; align-items:center; gap:10px; padding:9px 12px;
    border-radius:8px; margin-bottom:3px; font-size:.875rem; font-weight:500;
    color:#2A8A56 !important; text-decoration:none !important; cursor:pointer;
    transition:background .15s, color .15s;
}
.nav-item:hover { background:#E0F0E8; color:#1A5C38; text-decoration:none; }
.nav-item.active { background:#D1E7D9; color:#1A5C38; font-weight:600; }
.nav-icon { width:16px; flex-shrink:0; }
.nav-bar  { display:inline-block; width:3px; height:14px; border-radius:2px;
            background:#C4D4CC; vertical-align:middle; }
.nav-item.active .nav-bar { background:#1A5C38; }
.nav-soon { font-size:.62rem; background:#E8F5EE; color:#2A8A56; border-radius:4px;
            padding:1px 5px; margin-left:auto; font-weight:600; letter-spacing:.03em; }
</style>
""", unsafe_allow_html=True)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # Logo
    st.markdown("""
    <div class="sb-logo">
      <svg width="42" height="42" viewBox="0 0 54 54" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="sb-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%"   stop-color="#145232"/>
            <stop offset="100%" stop-color="#2A8A56"/>
          </linearGradient>
        </defs>
        <rect width="54" height="54" rx="14" fill="url(#sb-grad)"/>
        <polyline points="10,17 19,36 27,23 35,36 44,17"
          stroke="white" stroke-width="3.8" fill="none"
          stroke-linejoin="round" stroke-linecap="round"/>
        <circle cx="19" cy="36" r="2.8" fill="rgba(255,255,255,0.55)"/>
        <circle cx="35" cy="36" r="2.8" fill="rgba(255,255,255,0.55)"/>
        <line x1="10" y1="43" x2="44" y2="43"
          stroke="rgba(255,255,255,0.22)" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      <div class="sb-logo-text">
        <div class="sb-name">UniWallet</div>
        <div class="sb-sub">University of St. Gallen</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    st.page_link("app.py", label="Home")
    st.page_link("pages/1_Dashboard.py", label="Dashboard")
    st.page_link("pages/2_Prediction.py", label="Prediction")
    st.page_link("pages/3_Expense_Log.py", label="Expense Log")

    st.divider()

    # ── Sidebar filters ───────────────────────────────────────────────────────
    st.markdown("**Filters**")
    filter_cats = st.multiselect(
        "Categories", CATEGORIES, default=CATEGORIES, key="filter_cats"
    )

    df_all = load_expenses()
    if not df_all.empty:
        min_date = df_all["date"].min().date()
        max_date = df_all["date"].max().date()
    else:
        min_date = date.today().replace(day=1)
        max_date = date.today()

    filter_dates = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="filter_dates",
    )

    search_term = st.text_input("Search description", placeholder="e.g. Mensa, Coop…")

    st.divider()
    st.caption("v0.1 · HSG · Spring 2026")


# ── LOAD & FILTER DATA ────────────────────────────────────────────────────────
df_all = load_expenses()

# Apply sidebar filters
if not df_all.empty:
    d_start = pd.Timestamp(filter_dates[0]) if len(filter_dates) == 2 else df_all["date"].min()
    d_end   = pd.Timestamp(filter_dates[1]) if len(filter_dates) == 2 else df_all["date"].max()
    df = df_all[
        (df_all["date"] >= d_start) &
        (df_all["date"] <= d_end) &
        (df_all["category"].isin(filter_cats))
    ].copy()
    if search_term:
        df = df[df["description"].str.contains(search_term, case=False, na=False)]
else:
    df = df_all.copy()


# ── PAGE HEADER ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <div style="display:flex; align-items:center; gap:18px;">
    <svg width="54" height="54" viewBox="0 0 54 54" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
      <defs>
        <linearGradient id="lgbg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%"   stop-color="#145232"/>
          <stop offset="100%" stop-color="#2A8A56"/>
        </linearGradient>
        <filter id="shadow">
          <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="rgba(0,0,0,0.18)"/>
        </filter>
      </defs>
      <rect width="54" height="54" rx="14" fill="url(#lgbg)" filter="url(#shadow)"/>
      <polyline points="10,17 19,36 27,23 35,36 44,17"
        stroke="white" stroke-width="3.8" fill="none"
        stroke-linejoin="round" stroke-linecap="round"/>
      <circle cx="19" cy="36" r="2.8" fill="rgba(255,255,255,0.55)"/>
      <circle cx="35" cy="36" r="2.8" fill="rgba(255,255,255,0.55)"/>
      <line x1="10" y1="43" x2="44" y2="43"
        stroke="rgba(255,255,255,0.2)" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    <div>
      <h1>Expense Log</h1>
      <p>UniWallet &nbsp;·&nbsp; Add, manage, and analyse your expenses</p>
    </div>
  </div>
</div>""", unsafe_allow_html=True)


# ── KPI SUMMARY ───────────────────────────────────────────────────────────────
if not df.empty:
    expenses_only = df[df["amount"] < 0]
    income_only   = df[df["amount"] > 0]

    total_exp    = expenses_only["amount"].abs().sum()
    total_inc    = income_only["amount"].sum()
    n_entries    = len(df)
    avg_expense  = expenses_only["amount"].abs().mean() if len(expenses_only) else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Total Expenses</div>
            <div class="kpi-value neg">CHF {total_exp:,.2f}</div>
            <div class="kpi-sub">{len(expenses_only)} transaction(s)</div></div>""",
            unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Total Income</div>
            <div class="kpi-value pos">CHF {total_inc:,.2f}</div>
            <div class="kpi-sub">{len(income_only)} payment(s)</div></div>""",
            unsafe_allow_html=True)
    with c3:
        balance = total_inc - total_exp
        bal_class = "pos" if balance >= 0 else "neg"
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Net Balance</div>
            <div class="kpi-value {bal_class}">CHF {balance:,.2f}</div>
            <div class="kpi-sub">income − expenses</div></div>""",
            unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Avg. Expense</div>
            <div class="kpi-value neg">CHF {avg_expense:,.2f}</div>
            <div class="kpi-sub">per transaction</div></div>""",
            unsafe_allow_html=True)

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
else:
    st.info("No entries yet — add your first expense below.")


# ── ADD NEW EXPENSE ───────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">Add New Entry</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 3, 2])
    with col1:
        new_date = st.date_input("Date", value=date.today(), key="new_date")
    with col2:
        new_desc = st.text_input("Description", placeholder="e.g. Mensa HSG, SBB…", key="new_desc")
    with col3:
        new_cat  = st.selectbox("Category", CATEGORIES, key="new_cat")

    col4, col5, col6 = st.columns([2, 2, 3])
    with col4:
        new_currency = st.selectbox("Currency", CURRENCIES, key="new_currency")
    with col5:
        entry_type = st.radio("Type", ["Expense (−)", "Income (+)"],
                              horizontal=True, key="new_type")
    with col6:
        new_amount = st.number_input(
            "Amount", min_value=0.01, max_value=100000.0,
            value=10.00, step=0.50, format="%.2f", key="new_amount"
        )

    new_note = st.text_input("Note (optional)", placeholder="Any extra detail…", key="new_note")

    btn_col, _, _ = st.columns([1, 3, 3])
    with btn_col:
        submitted = st.button("Add Entry", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

if submitted:
    if not new_desc.strip():
        st.markdown('<div class="toast-err">Description cannot be empty.</div>',
                    unsafe_allow_html=True)
    else:
        signed_amount = -abs(new_amount) if "Expense" in entry_type else abs(new_amount)
        insert_expense(new_date, new_desc.strip(), new_cat,
                       new_currency, signed_amount, new_note.strip())
        st.markdown('<div class="toast-ok">Entry added successfully!</div>',
                    unsafe_allow_html=True)
        st.rerun()


# ── CHARTS ────────────────────────────────────────────────────────────────────
if not df.empty and len(df[df["amount"] < 0]) > 0:
    st.markdown('<div class="sec-header">Spending Overview</div>', unsafe_allow_html=True)

    expenses_df = df[df["amount"] < 0].copy()
    expenses_df["amount_abs"] = expenses_df["amount"].abs()

    ch1, ch2 = st.columns(2)

    # Pie: by category
    with ch1:
        cat_totals = expenses_df.groupby("category")["amount_abs"].sum().reset_index()
        fig_pie = px.pie(
            cat_totals, values="amount_abs", names="category",
            hole=0.45, color_discrete_sequence=CHART_COLORS,
            title="Expenses by Category",
        )
        fig_pie.update_traces(
            textposition="inside", textinfo="percent+label", textfont_size=11,
            hovertemplate="<b>%{label}</b><br>CHF %{value:,.2f}  (%{percent})<extra></extra>",
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#111111", size=12),
            height=360, margin=dict(t=50, b=20, l=10, r=10),
            title=dict(font=dict(size=13, color="#111111"), x=0),
            showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Bar: daily spending
    with ch2:
        daily_bar = (expenses_df.groupby("date")["amount_abs"].sum()
                     .reset_index().sort_values("date"))
        fig_bar = px.bar(
            daily_bar, x="date", y="amount_abs",
            labels={"date": "", "amount_abs": "CHF"},
            color_discrete_sequence=[GREEN_MID],
            title="Daily Spending",
        )
        fig_bar.update_traces(
            marker_line_width=0,
            hovertemplate="%{x|%d %b}<br>CHF %{y:,.2f}<extra></extra>",
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#111111", size=12),
            height=360, margin=dict(t=50, b=40, l=55, r=10),
            title=dict(font=dict(size=13, color="#111111"), x=0),
            xaxis=dict(showgrid=False, tickfont=dict(color="#111111")),
            yaxis=dict(showgrid=True, gridcolor="#E8F5EE",
                       tickfont=dict(color="#111111"),
                       title_font=dict(color="#111111")),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Cumulative line
    st.markdown('<div class="sec-header">Cumulative Spending Over Time</div>',
                unsafe_allow_html=True)
    daily_cum = daily_bar.copy().sort_values("date")
    daily_cum["cumulative"] = daily_cum["amount_abs"].cumsum()

    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(
        x=daily_cum["date"], y=daily_cum["cumulative"],
        mode="lines", fill="tozeroy",
        line=dict(color=GREEN_DARK, width=2.5),
        fillcolor="rgba(26,92,56,0.07)",
        hovertemplate="%{x|%d %b %Y}<br>Cumulative: CHF %{y:,.2f}<extra></extra>",
    ))
    fig_cum.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#111111", size=12),
        height=260, margin=dict(t=10, b=40, l=60, r=20),
        xaxis=dict(showgrid=False, title="",
                   tickfont=dict(color="#111111")),
        yaxis=dict(showgrid=True, gridcolor="#E8F5EE", title="CHF",
                   tickfont=dict(color="#111111"),
                   title_font=dict(color="#111111")),
    )
    st.plotly_chart(fig_cum, use_container_width=True)


# ── TRANSACTION TABLE ─────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">All Entries</div>', unsafe_allow_html=True)

if df.empty:
    st.markdown("""
    <div style="background:#F0FAF4; border:1.5px solid #D1E7D9; border-radius:12px;
                padding:32px; text-align:center; color:#5A6B6B;">
        <div style="font-size:2rem; margin-bottom:8px;"></div>
        <div style="font-weight:600; color:#1C2B2B; margin-bottom:4px;">No entries found</div>
        <div style="font-size:.85rem;">Add your first expense using the form above.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Sorting control
    sort_col, _, del_col = st.columns([2, 3, 2])
    with sort_col:
        sort_by = st.selectbox(
            "Sort by",
            ["Date (newest)", "Date (oldest)", "Amount (highest)", "Amount (lowest)", "Category"],
            key="sort_by",
        )
    with del_col:
        show_delete = st.toggle("Enable delete / edit", value=False, key="show_delete")

    sort_map = {
        "Date (newest)":   ("date", False),
        "Date (oldest)":   ("date", True),
        "Amount (highest)":("amount", False),
        "Amount (lowest)": ("amount", True),
        "Category":        ("category", True),
    }
    sort_field, sort_asc = sort_map[sort_by]
    df_sorted = df.sort_values(sort_field, ascending=sort_asc).reset_index(drop=True)

    # Display the dataframe
    display_df = df_sorted.copy()
    display_df["Date"]        = display_df["date"].dt.strftime("%d %b %Y")
    display_df["Amount (CHF)"] = display_df["amount"].apply(
        lambda x: f"+{x:,.2f}" if x > 0 else f"{x:,.2f}"
    )
    display_df["Note"] = display_df["note"].fillna("").replace("", "—")

    st.dataframe(
        display_df[["Date", "description", "category", "currency",
                    "Amount (CHF)", "Note"]].rename(
            columns={"description": "Description", "category": "Category",
                     "currency": "Ccy"}
        ),
        use_container_width=True,
        hide_index=True,
    )

    # ── Delete / Edit section ─────────────────────────────────────────────────
    if show_delete:
        st.markdown('<div class="sec-header">Edit or Delete an Entry</div>',
                    unsafe_allow_html=True)

        id_options = df_sorted["id"].tolist()
        label_map  = {
            row["id"]: f"#{row['id']}  {row['date'].strftime('%d %b %Y')}  |  "
                       f"{row['description']}  |  CHF {row['amount']:+,.2f}"
            for _, row in df_sorted.iterrows()
        }

        selected_id = st.selectbox(
            "Select entry",
            id_options,
            format_func=lambda i: label_map[i],
            key="edit_select",
        )

        sel_row = df_sorted[df_sorted["id"] == selected_id].iloc[0]

        edit_tab, del_tab = st.tabs(["Edit", "Delete"])

        with edit_tab:
            ec1, ec2, ec3 = st.columns([2, 3, 2])
            with ec1:
                e_date = st.date_input("Date", value=sel_row["date"].date(), key="e_date")
            with ec2:
                e_desc = st.text_input("Description", value=sel_row["description"], key="e_desc")
            with ec3:
                e_cat  = st.selectbox("Category", CATEGORIES,
                                      index=CATEGORIES.index(sel_row["category"])
                                      if sel_row["category"] in CATEGORIES else 0,
                                      key="e_cat")
            ec4, ec5, ec6 = st.columns([2, 2, 3])
            with ec4:
                e_ccy = st.selectbox("Currency", CURRENCIES,
                                     index=CURRENCIES.index(sel_row["currency"])
                                     if sel_row["currency"] in CURRENCIES else 0,
                                     key="e_ccy")
            with ec5:
                e_type = st.radio(
                    "Type",
                    ["Expense (−)", "Income (+)"],
                    index=0 if sel_row["amount"] < 0 else 1,
                    horizontal=True, key="e_type",
                )
            with ec6:
                e_amount = st.number_input(
                    "Amount", min_value=0.01, max_value=100000.0,
                    value=abs(float(sel_row["amount"])),
                    step=0.50, format="%.2f", key="e_amount",
                )
            e_note = st.text_input("Note", value=sel_row["note"] or "", key="e_note")

            if st.button("Save Changes", key="save_edit"):
                if not e_desc.strip():
                    st.markdown('<div class="toast-err">Description cannot be empty.</div>',
                                unsafe_allow_html=True)
                else:
                    signed = -abs(e_amount) if "Expense" in e_type else abs(e_amount)
                    update_expense(selected_id, e_date, e_desc.strip(),
                                   e_cat, e_ccy, signed, e_note.strip())
                    st.markdown('<div class="toast-ok">Entry updated.</div>',
                                unsafe_allow_html=True)
                    st.rerun()

        with del_tab:
            st.warning(
                f"You are about to permanently delete entry **#{selected_id}** — "
                f"**{sel_row['description']}** on {sel_row['date'].strftime('%d %b %Y')} "
                f"(CHF {sel_row['amount']:+,.2f}). This cannot be undone."
            )
            if st.button("Confirm Delete", key="confirm_delete"):
                delete_expense(selected_id)
                st.markdown('<div class="toast-ok">Entry deleted.</div>',
                            unsafe_allow_html=True)
                st.rerun()

    # ── CSV Export ────────────────────────────────────────────────────────────
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    export_df = df_sorted[["date", "description", "category",
                            "currency", "amount", "note"]].copy()
    export_df["date"] = export_df["date"].dt.strftime("%Y-%m-%d")
    csv_data = export_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Export to CSV",
        data=csv_data,
        file_name=f"uniwallet_expenses_{date.today().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "UniWallet · Fundamentals & Methods of CS · University of St. Gallen · Spring 2026"
)