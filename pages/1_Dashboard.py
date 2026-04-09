# =============================================================================
# UniWallet — Dashboard
# University of St. Gallen  ·  Fundamentals & Methods of CS  ·  Spring 2026
# =============================================================================
# HOW TO RUN:
#   pip install streamlit plotly pandas numpy requests
#   streamlit run dashboard.py
# =============================================================================

import calendar
from datetime import datetime, timedelta
import random

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="UniWallet", page_icon="W", layout="wide")

# ── COLOUR PALETTE ────────────────────────────────────────────────────────────
GREEN_DARK   = "#1A5C38"
GREEN_MID    = "#2A8A56"
GREEN_LIGHT  = "#4DB87A"
EUR_COLOR    = "#3B82F6"   # blue accent for EUR-denominated items
CHART_COLORS = ["#1A5C38", "#2A8A56", "#4DB87A", "#7FCF9F", "#B2E4C8", "#D5F0E2"]

# ── LIVE EXCHANGE RATES (cached 1 h) ─────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_rates(base: str = "CHF") -> dict:
    """Pull FX rates from frankfurter.app (free, no key required)."""
    try:
        r = requests.get(f"https://api.frankfurter.app/latest?from={base}", timeout=5)
        return r.json().get("rates", {})
    except Exception:
        # Values = how many units of that currency 1 CHF buys.
        # CHF is stronger than EUR: 1 CHF ≈ 1.056 EUR, so 1 EUR ≈ 0.947 CHF.
        return {"EUR": 1.056, "USD": 1.112, "GBP": 0.874,
                "JPY": 168.4, "SEK": 11.6, "CAD": 1.52, "AUD": 1.71}

rates_from_chf = fetch_rates("CHF")
# EUR→CHF: how many CHF one Euro buys (< 1 because CHF is stronger)
EUR_TO_CHF = round(1.0 / rates_from_chf.get("EUR", 1.056), 4)
# Static rate baked into sample data (keeps the cached DataFrame stable)
EUR_TO_CHF_DATA = 0.947


# ── SAMPLE DATA ───────────────────────────────────────────────────────────────
@st.cache_data
def generate_sample_transactions() -> pd.DataFrame:
    """
    90 days of realistic transactions for a German HSG student in St. Gallen.
    Parental allowance arrives in EUR; everything else is CHF.
    Columns: date, description, category, currency, amount_original, amount (CHF).
    """
    daily_cats = {
        "Food & Drinks": {
            "vendors": ["Mensa HSG", "Migros", "Coop", "Starbucks", "Uni Café",
                        "Döner Laden", "Manor Food"],
            "range": (6, 20), "weight": 5,
        },
        "Transport": {
            "vendors": ["SBB Tageskarte", "PostAuto", "Lime Scooter", "SBB Halbtageskarte"],
            "range": (4, 26), "weight": 2,
        },
        "Entertainment": {
            "vendors": ["Cinema Scala", "Bar 7", "Netflix", "Book Store", "Konzert Tonhalle"],
            "range": (9, 40), "weight": 1,
        },
        "Shopping": {
            "vendors": ["Digitec", "H&M", "Zalando", "Interdiscount", "IKEA Konstanz"],
            "range": (18, 75), "weight": 1,
        },
        "Education": {
            "vendors": ["Print Shop HSG", "Textbook", "Coursera"],
            "range": (5, 35), "weight": 1,
        },
    }
    cat_names   = list(daily_cats.keys())
    cat_weights = [daily_cats[c]["weight"] for c in cat_names]

    random.seed(7)
    rows = []

    # --- Variable daily spending (all CHF) ---
    for i in range(90):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        n = random.choices([0, 1, 2], weights=[15, 65, 20])[0]
        for _ in range(n):
            cat  = random.choices(cat_names, weights=cat_weights)[0]
            info = daily_cats[cat]
            amt  = -round(random.uniform(*info["range"]), 2)
            rows.append({"date": date_str, "description": random.choice(info["vendors"]),
                         "category": cat, "currency": "CHF",
                         "amount_original": amt, "amount": amt})

    # --- Fixed monthly costs (CHF) ---
    for i in range(0, 90, 30):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        for desc, amt in [
            ("WG Miete",            -780.00),
            ("Krankenkasse Prämie", -310.00),
            ("Swisscom Mobile",      -49.00),
            ("Spotify",              -12.90),
        ]:
            rows.append({"date": date_str, "description": desc, "category": "Utilities",
                         "currency": "CHF", "amount_original": amt, "amount": amt})

    # --- Semester fee (CHF, once) ---
    rows.append({
        "date": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
        "description": "HSG Semester Fee", "category": "Education",
        "currency": "CHF", "amount_original": -650.00, "amount": -650.00,
    })

    # --- Monthly income ---
    for i in range(0, 90, 30):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")

        # Parental allowance arrives in EUR (German parents → German bank → CHF account)
        eur_orig = 1800.00
        rows.append({
            "date": date_str, "description": "Eltern Überweisung",
            "category": "Income", "currency": "EUR",
            "amount_original": eur_orig,
            "amount": round(eur_orig * EUR_TO_CHF_DATA, 2),   # stored as CHF
        })

        # Part-time job paid in CHF
        rows.append({
            "date": date_str, "description": "Studentenjob Lohn",
            "category": "Income", "currency": "CHF",
            "amount_original": 700.00, "amount": 700.00,
        })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date", ascending=False).reset_index(drop=True)


df_all = generate_sample_transactions()


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

/* ── Forecast banner ── */
.forecast-banner {
    background: linear-gradient(120deg, #1A5C38 0%, #2A8A56 100%);
    border-radius: 12px; padding: 22px 26px; color: white;
}
.forecast-banner .fb-label { font-size: .7rem; font-weight: 600; text-transform: uppercase;
                              letter-spacing: .08em; opacity: .8; }
.forecast-banner .fb-value { font-size: 2.1rem; font-weight: 700; margin: 6px 0 4px; }
.forecast-banner .fb-note  { font-size: .8rem; opacity: .75; }

/* ── FX panel cards ── */
.fx-rate-banner {
    background: linear-gradient(120deg, #1E3A8A 0%, #3B82F6 100%);
    border-radius: 12px; padding: 22px 26px; color: white; text-align: center;
}
.fx-rate-banner .fx-label { font-size: .7rem; font-weight: 600; text-transform: uppercase;
                             letter-spacing: .08em; opacity: .8; }
.fx-rate-banner .fx-rate  { font-size: 2.4rem; font-weight: 700; margin: 6px 0 2px; }
.fx-rate-banner .fx-sub   { font-size: .8rem; opacity: .75; }

.calc-box {
    background: #F0FAF4; border: 1.5px solid #D1E7D9; border-radius: 12px; padding: 20px;
}
.calc-result {
    background: white; border: 1.5px solid #D1E7D9; border-radius: 10px;
    padding: 16px; margin-top: 10px; text-align: center;
}
.calc-result .cr-val   { font-size: 2rem; font-weight: 700; color: #1A5C38; }
.calc-result .cr-note  { font-size: .78rem; color: #5A6B6B; margin-top: 4px; }

.sensitivity-row {
    display: flex; gap: 10px; margin-top: 10px;
}
.sens-card {
    flex: 1; background: white; border-radius: 8px; padding: 12px;
    border: 1px solid #D1E7D9; text-align: center; font-size: .8rem;
}
.sens-card .sc-label { color: #5A6B6B; font-size: .68rem; margin-bottom: 4px;
                       text-transform: uppercase; letter-spacing: .05em; }
.sens-card .sc-val   { font-weight: 700; font-size: 1rem; }
.up   { color: #1A5C38; }
.down { color: #9CA3AF; }

/* ── EUR badge in transaction table ── */
.eur-badge {
    background: #DBEAFE; color: #1D4ED8; font-size: .68rem; font-weight: 600;
    border-radius: 4px; padding: 2px 6px; margin-left: 4px;
}

/* ── Widget accent → green ── */
[data-testid="stSlider"] [role="slider"] { background: #1A5C38 !important; border-color: #1A5C38 !important; }

/* Multiselect selected tags — light green pill */
[data-baseweb="tag"] { background-color: #E8F5EE !important; color: #1A5C38 !important;
                       border: 1px solid #B2DEC7 !important; }
[data-baseweb="tag"] span { color: #1A5C38 !important; }
[data-baseweb="tag"] button path { fill: #1A5C38 !important; }

/* Selectbox / multiselect container + selected value text — always dark */
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

/* ── Dataframe — white container, natural internal rendering ── */
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

/* ── Sidebar logo ── */
.sb-logo { display:flex; align-items:center; gap:12px; padding-bottom:18px;
           border-bottom:1px solid #D1E7D9; margin-bottom:6px; }
.sb-logo-text .sb-name { font-size:1.15rem; font-weight:700; color:#1A5C38; line-height:1.2; }
.sb-logo-text .sb-sub  { font-size:.68rem; color:#5A6B6B; letter-spacing:.03em; }

/* ── Sidebar nav ── */
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

/* ── Budget status bar ── */
.budget-wrap {
    background:white; border:1.5px solid #D1E7D9; border-radius:12px;
    padding:16px 20px; margin:1rem 0 .5rem;
}
.budget-header { display:flex; justify-content:space-between; align-items:baseline;
                 font-size:.78rem; margin-bottom:8px; }
.budget-header .bh-label { font-weight:600; color:#1C2B2B; }
.budget-header .bh-nums  { color:#5A6B6B; font-size:.75rem; }
.budget-track  { height:9px; background:#E8F5EE; border-radius:99px; overflow:hidden; }
.budget-fill   { height:100%; border-radius:99px; transition:width .4s; }
.b-ok     { background:linear-gradient(90deg,#1A5C38,#4DB87A); }
.b-warn   { background:linear-gradient(90deg,#B45309,#F59E0B); }
.b-breach { background:linear-gradient(90deg,#5B21B6,#8B5CF6); }
.budget-footer { display:flex; justify-content:space-between; margin-top:7px;
                 font-size:.72rem; color:#5A6B6B; }
.badge {
    display:inline-block; font-size:.7rem; font-weight:700; border-radius:6px;
    padding:3px 10px; letter-spacing:.03em;
}
.badge-ok     { background:#D1E7D9; color:#1A5C38; }
.badge-warn   { background:#FEF3C7; color:#92400E; }
.badge-breach { background:#EDE9FE; color:#5B21B6; }
</style>
""", unsafe_allow_html=True)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # ── Logo ─────────────────────────────────────────────────────────────────
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

    # ── Navigation ───────────────────────────────────────────────────────────
    st.page_link("app.py", label="Home")
    st.page_link("pages/1_Dashboard.py", label="Dashboard")
    st.page_link("pages/2_Prediction.py", label="Prediction")
    st.page_link("pages/3_Expense_Log.py", label="Expense Log")

    st.divider()

    # ── Budget ───────────────────────────────────────────────────────────────
    st.markdown("**Monthly Budget**")
    monthly_budget = st.number_input(
        "Budget (CHF)", min_value=0, max_value=10000,
        value=2000, step=50, label_visibility="collapsed"
    )

    st.divider()

    # ── Filters ──────────────────────────────────────────────────────────────
    st.markdown("**Filters**")
    expense_cats  = sorted(df_all[df_all["category"] != "Income"]["category"].unique().tolist())
    selected_cats = st.multiselect("Categories", expense_cats, default=expense_cats)
    date_range    = st.date_input(
        "Date range",
        value=(df_all["date"].min().date(), df_all["date"].max().date()),
        min_value=df_all["date"].min().date(),
        max_value=df_all["date"].max().date(),
    )

    st.divider()
    st.caption("v0.1 · HSG · Spring 2026")

# Apply filters
d_start = pd.Timestamp(date_range[0]) if len(date_range) == 2 else df_all["date"].min()
d_end   = pd.Timestamp(date_range[1]) if len(date_range) == 2 else df_all["date"].max()

df = df_all[
    (df_all["date"] >= d_start) & (df_all["date"] <= d_end) &
    (df_all["category"].isin(selected_cats + ["Income"]))
].copy()

expenses_df = df[df["amount"] < 0].copy()
expenses_df["amount"] = expenses_df["amount"].abs()


# ── KEY METRICS ───────────────────────────────────────────────────────────────
total_income    = df[df["amount"] > 0]["amount"].sum()
total_expenses  = df[df["amount"] < 0]["amount"].sum()
current_balance = total_income + total_expenses
n_income_rows   = int((df["amount"] > 0).sum())
n_expense_rows  = int((df["amount"] < 0).sum())
this_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
this_month_exp   = df[(df["amount"] < 0) & (df["date"] >= this_month_start)]["amount"].sum()

# EUR-specific income metrics
eur_income_df      = df[(df["amount"] > 0) & (df["currency"] == "EUR")]
eur_received_orig  = eur_income_df["amount_original"].sum()   # total € received
eur_received_chf   = eur_income_df["amount"].sum()             # CHF equivalent at data rate
n_eur_transfers    = len(eur_income_df)


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
      <h1>UniWallet</h1>
      <p>University of St. Gallen &nbsp;·&nbsp; Track, analyse, and forecast your student finances</p>
    </div>
  </div>
</div>""", unsafe_allow_html=True)


# ── KPI CARDS ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Current Balance</div>
        <div class="kpi-value pos">CHF {current_balance:,.2f}</div>
        <div class="kpi-sub">90-day window</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Total Income</div>
        <div class="kpi-value pos">CHF {total_income:,.2f}</div>
        <div class="kpi-sub">{n_income_rows} payment(s)</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Total Expenses</div>
        <div class="kpi-value neg">CHF {abs(total_expenses):,.2f}</div>
        <div class="kpi-sub">{n_expense_rows} transactions</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">This Month</div>
        <div class="kpi-value neg">CHF {abs(this_month_exp):,.2f}</div>
        <div class="kpi-sub">spending so far</div></div>""", unsafe_allow_html=True)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# ── BUDGET STATUS BAR ─────────────────────────────────────────────────────────
spent        = abs(this_month_exp)
pct          = min(spent / monthly_budget * 100, 100) if monthly_budget > 0 else 0
over_budget  = spent > monthly_budget and monthly_budget > 0
near_budget  = pct >= 80 and not over_budget

if monthly_budget > 0:
    if over_budget:
        fill_class  = "b-breach"
        badge_class = "badge-breach"
        badge_text  = "Budget Exceeded"
        status_note = f"CHF {spent - monthly_budget:,.2f} over your monthly limit"
    elif near_budget:
        fill_class  = "b-warn"
        badge_class = "badge-warn"
        badge_text  = "Approaching Limit"
        status_note = f"CHF {monthly_budget - spent:,.2f} remaining — spend carefully"
    else:
        fill_class  = "b-ok"
        badge_class = "badge-ok"
        badge_text  = "On Track"
        status_note = f"CHF {monthly_budget - spent:,.2f} remaining this month"

    st.markdown(f"""
    <div class="budget-wrap">
      <div class="budget-header">
        <span class="bh-label">Monthly Budget &nbsp;<span class="badge {badge_class}">{badge_text}</span></span>
        <span class="bh-nums">CHF {spent:,.2f} / CHF {monthly_budget:,.0f}</span>
      </div>
      <div class="budget-track">
        <div class="budget-fill {fill_class}" style="width:{pct:.1f}%"></div>
      </div>
      <div class="budget-footer">
        <span>{status_note}</span>
        <span>{pct:.0f}% used</span>
      </div>
    </div>""", unsafe_allow_html=True)


# ── CHART ROW 1: PIE + BAR ────────────────────────────────────────────────────
st.markdown('<div class="sec-header">Spending Breakdown</div>', unsafe_allow_html=True)

category_totals = expenses_df.groupby("category")["amount"].sum().reset_index()
pie_col, bar_col = st.columns(2)

with pie_col:
    fig_pie = px.pie(
        category_totals, values="amount", names="category",
        hole=0.45, color_discrete_sequence=CHART_COLORS, title="Spending by Category",
    )
    fig_pie.update_traces(
        textposition="inside", textinfo="percent+label", textfont_size=11,
        hovertemplate="<b>%{label}</b><br>CHF %{value:,.2f}  (%{percent})<extra></extra>",
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#111111", size=12),
        height=370, margin=dict(t=50, b=20, l=10, r=10),
        title=dict(font=dict(size=13, color="#111111"), x=0), showlegend=False,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with bar_col:
    st.markdown("**Daily Totals by Month**")
    available_months = sorted(expenses_df["date"].dt.to_period("M").unique(), reverse=True)
    month_labels = [m.strftime("%B %Y") for m in available_months]
    month_keys   = [str(m) for m in available_months]
    sel_idx = st.selectbox("Month", range(len(month_labels)),
                           format_func=lambda i: month_labels[i], key="bar_month")
    month_data = expenses_df[
        expenses_df["date"].dt.to_period("M").astype(str) == month_keys[sel_idx]
    ]
    daily_bar = month_data.groupby("date")["amount"].sum().reset_index()
    fig_bar = px.bar(daily_bar, x="date", y="amount",
                     labels={"date": "", "amount": "CHF"},
                     color_discrete_sequence=[GREEN_MID])
    fig_bar.update_traces(marker_line_width=0,
                          hovertemplate="%{x|%d %b}<br>CHF %{y:,.2f}<extra></extra>")
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#111111", size=12),
        height=330, margin=dict(t=10, b=40, l=55, r=10),
        xaxis=dict(showgrid=False, tickfont=dict(color="#111111")),
        yaxis=dict(showgrid=True, gridcolor="#E8F5EE",
                   tickfont=dict(color="#111111"), title_font=dict(color="#111111")),
    )
    st.plotly_chart(fig_bar, use_container_width=True)


# ── CHART ROW 2: CUMULATIVE LINE ──────────────────────────────────────────────
st.markdown('<div class="sec-header">Cumulative Spending Over Time</div>', unsafe_allow_html=True)

daily_cum = (expenses_df.groupby("date")["amount"].sum()
             .reset_index().sort_values("date"))
daily_cum["cumulative"] = daily_cum["amount"].cumsum()

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
    height=290, margin=dict(t=10, b=40, l=60, r=20),
    xaxis=dict(showgrid=False, title="", tickfont=dict(color="#111111")),
    yaxis=dict(showgrid=True, gridcolor="#E8F5EE", title="CHF",
               tickfont=dict(color="#111111"), title_font=dict(color="#111111")),
)
st.plotly_chart(fig_cum, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ── FOREIGN INCOME & EXCHANGE ─────────────────────────────────────────────────
# Many HSG students receive EUR allowances from abroad (e.g. German parents)
# but live and spend in CHF. This section makes that visible.
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-header">Foreign Income &amp; Exchange</div>',
            unsafe_allow_html=True)

fx_left, fx_right = st.columns([3, 2])

with fx_left:
    # Three mini KPIs about EUR income
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">EUR Received (90d)</div>
            <div class="kpi-value blue">€ {eur_received_orig:,.0f}</div>
            <div class="kpi-sub">{n_eur_transfers} transfer(s)</div></div>""",
            unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">CHF Equivalent</div>
            <div class="kpi-value pos">CHF {eur_received_chf:,.0f}</div>
            <div class="kpi-sub">at booking rate</div></div>""",
            unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Live EUR → CHF</div>
            <div class="kpi-value blue">{EUR_TO_CHF:.4f}</div>
            <div class="kpi-sub">1 EUR in CHF · now</div></div>""",
            unsafe_allow_html=True)

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

    # Stacked bar: EUR-sourced vs CHF-sourced income by month
    income_df = df[df["amount"] > 0].copy()
    income_df["month"] = income_df["date"].dt.to_period("M").dt.strftime("%b %Y")
    income_df["source"] = income_df["currency"].map(
        {"EUR": "EUR (converted to CHF)", "CHF": "CHF income"}
    )
    inc_grouped = (income_df.groupby(["month", "source"])["amount"]
                   .sum().reset_index()
                   .sort_values("month"))

    fig_inc = go.Figure()
    for src, color in [("CHF income", GREEN_DARK), ("EUR (converted to CHF)", EUR_COLOR)]:
        sub = inc_grouped[inc_grouped["source"] == src]
        fig_inc.add_trace(go.Bar(
            x=sub["month"], y=sub["amount"], name=src,
            marker_color=color,
            hovertemplate="%{x}<br>CHF %{y:,.2f}<extra></extra>",
        ))
    fig_inc.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#111111", size=12),
        height=220, margin=dict(t=10, b=40, l=55, r=10),
        legend=dict(orientation="h", y=-0.28, font=dict(size=11, color="#111111")),
        xaxis=dict(showgrid=False, tickfont=dict(color="#111111")),
        yaxis=dict(showgrid=True, gridcolor="#E8F5EE", title="CHF",
                   tickfont=dict(color="#111111"), title_font=dict(color="#111111")),
    )
    st.plotly_chart(fig_inc, use_container_width=True)

    # ── Top categories this month ─────────────────────────────────────────────
    st.markdown("""<div style='font-size:.75rem; font-weight:600; text-transform:uppercase;
        letter-spacing:.07em; color:#5A6B6B; margin-bottom:8px;'>Top Categories This Month</div>""",
        unsafe_allow_html=True)

    this_m_exp = expenses_df[expenses_df["date"] >= this_month_start].copy()
    top_cats   = (this_m_exp.groupby("category")["amount"]
                  .sum().sort_values(ascending=False).head(5).reset_index())
    max_amt    = top_cats["amount"].max() if len(top_cats) else 1

    rows_html = ""
    for _, row in top_cats.iterrows():
        bar_pct = row["amount"] / max_amt * 100
        rows_html += f"""
        <div style="margin-bottom:10px;">
          <div style="display:flex; justify-content:space-between; font-size:.78rem;
                      margin-bottom:4px; color:#1C2B2B;">
            <span style="font-weight:500;">{row['category']}</span>
            <span style="color:#5A6B6B; font-weight:600;">CHF {row['amount']:,.2f}</span>
          </div>
          <div style="height:6px; background:#E8F5EE; border-radius:99px; overflow:hidden;">
            <div style="width:{bar_pct:.1f}%; height:100%; background:#2A8A56;
                        border-radius:99px;"></div>
          </div>
        </div>"""
    st.markdown(f'<div style="background:white; border:1.5px solid #D1E7D9; border-radius:12px; padding:16px 18px;">{rows_html}</div>',
                unsafe_allow_html=True)

with fx_right:
    # ── Live rate banner ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="fx-rate-banner">
        <div class="fx-label">Live Exchange Rate</div>
        <div class="fx-rate">1 EUR = {EUR_TO_CHF:.4f} CHF</div>
        <div class="fx-sub">Source: frankfurter.app &nbsp;·&nbsp; refreshed hourly</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Allowance calculator ──────────────────────────────────────────────────
    st.markdown('<div class="calc-box">', unsafe_allow_html=True)
    st.markdown("**Allowance Calculator**")
    st.caption("How much CHF does your EUR allowance actually buy?")

    eur_input = st.number_input(
        "Monthly allowance (EUR)", min_value=100.0, max_value=10000.0,
        value=1800.0, step=50.0, format="%.0f", key="eur_calc"
    )
    chf_equiv         = eur_input * EUR_TO_CHF
    fixed_costs_chf   = 780 + 310 + 49 + 12.90   # WG + insurance + phone + Spotify
    free_after_fixed  = chf_equiv - fixed_costs_chf

    st.markdown(f"""
    <div class="calc-result">
        <div class="cr-val">CHF {chf_equiv:,.2f}</div>
        <div class="cr-note">
            After fixed costs (CHF {fixed_costs_chf:,.0f}):
            <strong>CHF {free_after_fixed:,.2f}</strong> discretionary
        </div>
    </div>""", unsafe_allow_html=True)

    # Exchange-rate sensitivity: ±5 %
    delta = eur_input * EUR_TO_CHF * 0.05
    st.markdown(f"""
    <div class="sensitivity-row">
        <div class="sens-card">
            <div class="sc-label">EUR +5 %</div>
            <div class="sc-val up">+CHF {delta:,.0f}</div>
        </div>
        <div class="sens-card">
            <div class="sc-label">EUR −5 %</div>
            <div class="sc-val down">−CHF {delta:,.0f}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Quick converter for any amount / any currency
    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
    st.markdown("**Quick Convert to CHF**")
    qc1, qc2 = st.columns([2, 2])
    with qc1:
        other_amt = st.number_input("Amount", min_value=0.0, value=50.0,
                                    step=1.0, format="%.2f", key="qc_amt")
    with qc2:
        other_ccy = st.selectbox("Currency", sorted(rates_from_chf.keys()),
                                 index=sorted(rates_from_chf.keys()).index("EUR")
                                       if "EUR" in rates_from_chf else 0,
                                 key="qc_ccy")
    if other_ccy in rates_from_chf:
        chf_result = other_amt / rates_from_chf[other_ccy]
        st.markdown(f"""
        <div style="background:#F0FAF4; border:1px solid #D1E7D9; border-radius:8px;
                    padding:10px; text-align:center; margin-top:4px;">
            <span style="font-size:1.3rem; font-weight:700; color:#1A5C38;">
                CHF {chf_result:,.2f}
            </span><br>
            <span style="font-size:.72rem; color:#5A6B6B;">
                1 {other_ccy} = CHF {1/rates_from_chf[other_ccy]:.4f}
            </span>
        </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ── ML FORECAST ───────────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">Month-End Forecast</div>', unsafe_allow_html=True)

fc_left, fc_right = st.columns([1, 2])

with fc_left:
    today        = datetime.now()
    month_start  = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_exp_df = expenses_df[expenses_df["date"] >= month_start].copy()

    if len(month_exp_df) >= 3:
        daily_m = (month_exp_df.groupby("date")["amount"].sum()
                   .reset_index().sort_values("date"))
        daily_m["day"] = daily_m["date"].dt.day
        x = daily_m["day"].values.astype(float)
        y = daily_m["amount"].cumsum().values

        coeffs          = np.polyfit(x, y, 1)
        days_in_month   = calendar.monthrange(today.year, today.month)[1]
        projected_total = float(np.polyval(coeffs, days_in_month))
        days_remaining  = days_in_month - today.day
        avg_daily       = y[-1] / today.day if today.day > 0 else 0.0

        st.markdown(f"""
        <div class="forecast-banner">
            <div class="fb-label">Projected Total — {today.strftime("%B %Y")}</div>
            <div class="fb-value">CHF {abs(projected_total):,.2f}</div>
            <div class="fb-note">
                {days_remaining} days remaining &nbsp;·&nbsp; avg CHF {avg_daily:.2f}/day
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("Not enough data this month yet.")

with fc_right:
    if len(month_exp_df) >= 3:
        future_days  = list(range(today.day + 1, days_in_month + 1))
        future_cumul = [float(np.polyval(coeffs, d)) for d in future_days]

        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(
            x=daily_m["day"].tolist(), y=y.tolist(),
            mode="lines+markers", name="Actual",
            line=dict(color=GREEN_DARK, width=2.5), marker=dict(size=6),
        ))
        if future_days:
            fig_fc.add_trace(go.Scatter(
                x=future_days, y=future_cumul,
                mode="lines", name="Forecast",
                line=dict(color=GREEN_LIGHT, width=2, dash="dash"),
            ))
        fig_fc.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#111111", size=11),
            height=220, margin=dict(t=12, b=30, l=55, r=10),
            legend=dict(orientation="h", y=-0.28, font=dict(size=11, color="#111111")),
            xaxis=dict(showgrid=False, title="Day of month",
                       tickfont=dict(color="#111111"), title_font=dict(color="#111111")),
            yaxis=dict(showgrid=True, gridcolor="#E8F5EE", title="CHF",
                       tickfont=dict(color="#111111"), title_font=dict(color="#111111")),
        )
        st.plotly_chart(fig_fc, use_container_width=True)


# ── RECENT TRANSACTIONS ───────────────────────────────────────────────────────
st.markdown('<div class="sec-header">Recent Transactions</div>', unsafe_allow_html=True)

n_rows = st.slider("Rows to display", 5, 50, 15)
recent = df.head(n_rows).copy()
recent["Date"] = recent["date"].dt.strftime("%d %b %Y")

# Show original currency for EUR transactions; CHF for everything else
def fmt_amount(row):
    if row["currency"] == "EUR":
        sign = "+" if row["amount"] > 0 else "−"
        return f"€ {sign}{abs(row['amount_original']):,.2f} → CHF {row['amount']:+,.2f}"
    else:
        return f"CHF {row['amount']:+,.2f}"

recent["Amount"] = recent.apply(fmt_amount, axis=1)

st.dataframe(
    recent[["Date", "description", "category", "currency", "Amount"]].rename(
        columns={"description": "Description", "category": "Category",
                 "currency": "Ccy"}
    ),
    use_container_width=True, hide_index=True,
)


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "UniWallet · Fundamentals & Methods of CS · University of St. Gallen · Spring 2026"
)
