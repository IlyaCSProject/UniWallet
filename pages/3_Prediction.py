# =============================================================================
# UniWallet — Prediction Page
# University of St. Gallen  ·  Fundamentals & Methods of CS  ·  Spring 2026
# =============================================================================
# PURPOSE:
#   This page uses a Linear Regression model (scikit-learn) trained on the
#   user's daily spending history to predict their total spending by month-end.
#   The forecast is colour-coded green (under budget) or red (over budget).
#
# HOW TO RUN:
#   streamlit run pages/3_Prediction.py
# =============================================================================

import calendar
from datetime import datetime, timedelta
import random

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression  # ML model

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="UniWallet · Prediction", page_icon="📈", layout="wide")

# ── COLOUR PALETTE (matches dashboard.py) ────────────────────────────────────
GREEN_DARK   = "#1A5C38"
GREEN_MID    = "#2A8A56"
GREEN_LIGHT  = "#4DB87A"

# ── CSS STYLING (matches dashboard.py exactly) ───────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: #FFFFFF !important;
    color: #1C2B2B;
}
.kpi-card {
    background: #FFFFFF; border: 1.5px solid #D1E7D9; border-radius: 12px;
    padding: 20px; text-align: center; box-shadow: 0 2px 10px rgba(26,92,56,.07);
    transition: box-shadow .2s, transform .2s; min-height: 104px;
    display: flex; flex-direction: column; justify-content: center;
}
.kpi-card:hover { box-shadow: 0 6px 18px rgba(26,92,56,.13); transform: translateY(-2px); }
.kpi-label { font-size: .7rem; font-weight: 600; text-transform: uppercase;
             letter-spacing: .08em; color: #5A6B6B; margin-bottom: 6px; }
.kpi-value { font-size: 1.65rem; font-weight: 700; line-height: 1.1; }
.pos  { color: #1A5C38; }
.neg  { color: #C0392B; }
.sec-header {
    font-size: 1rem; font-weight: 600; color: #1C2B2B;
    border-left: 4px solid #1A5C38; padding-left: 12px;
    margin-top: 2rem; margin-bottom: .75rem;
}
.page-header {
    background: linear-gradient(120deg, #1A5C38 0%, #2A8A56 100%);
    border-radius: 14px; padding: 28px 36px; margin-bottom: 1.5rem;
}
.page-header h1 { font-size: 1.7rem; font-weight: 700; margin: 0; color: white; }
.page-header p  { margin: 6px 0 0; font-size: .88rem; opacity: .8; color: white; }

/* ── Forecast banner — made bigger ── */
.forecast-banner {
    background: linear-gradient(135deg, #1A5C38 0%, #2A8A56 100%);
    border-radius: 16px; padding: 36px 36px; color: white; margin-bottom: 1rem;
    min-height: 260px; display: flex; flex-direction: column; justify-content: center;
}
.forecast-banner.over-budget {
    background: linear-gradient(135deg, #922B21 0%, #C0392B 100%);
}
.fb-label  { font-size: .78rem; font-weight: 600; text-transform: uppercase;
             letter-spacing: .08em; opacity: .8; margin-bottom: 12px; }
.fb-value  { font-size: 3.2rem; font-weight: 700; line-height: 1.1; margin-bottom: 14px; }
.fb-status { font-size: 1rem; opacity: .95; margin-bottom: 8px; font-weight: 500; }
.fb-note   { font-size: .88rem; opacity: .8; margin-bottom: 20px; }

/* ── Progress bar ── */
.progress-wrap {
    background: rgba(255,255,255,0.25); border-radius: 99px; height: 14px;
    overflow: hidden; margin: 10px 0 6px;
}
.progress-fill { height: 100%; border-radius: 99px; background: white; transition: width .4s ease; }
.progress-label { font-size: .78rem; opacity: .85; }

/* ── Tip box ── */
.tip-box {
    background: #F0FAF4; border: 1.5px solid #D1E7D9;
    border-radius: 10px; padding: 14px 18px;
    font-size: .83rem; color: #1C2B2B; margin-top: .75rem;
}
</style>
""", unsafe_allow_html=True)


# ── SAMPLE DATA ───────────────────────────────────────────────────────────────
# Same generator as dashboard.py so both pages show consistent data
# while the real SQLite database is not yet connected.
EUR_TO_CHF_DATA = 0.947

@st.cache_data
def generate_sample_transactions() -> pd.DataFrame:
    """
    Generates realistic sample transactions spread across the current month.
    Daily spending is ~CHF 35-45/day so the forecast looks realistic (~CHF 1,250).
    Used as fallback when the SQLite database is not available.
    """
    daily_cats = {
        "Food & Drinks":  {"vendors": ["Mensa HSG","Migros","Coop","Starbucks","Uni Café","Döner Laden"], "range": (8, 18),  "weight": 5},
        "Transport":      {"vendors": ["SBB Tageskarte","PostAuto","Lime Scooter"],                        "range": (4, 16),  "weight": 2},
        "Entertainment":  {"vendors": ["Cinema Scala","Bar 7","Netflix","Book Store"],                     "range": (9, 25),  "weight": 1},
        "Shopping":       {"vendors": ["Digitec","H&M","Zalando","IKEA Konstanz"],                         "range": (15, 40), "weight": 1},
        "Education":      {"vendors": ["Print Shop HSG","Textbook","Coursera"],                            "range": (5, 20),  "weight": 1},
    }
    cat_names   = list(daily_cats.keys())
    cat_weights = [daily_cats[c]["weight"] for c in cat_names]
    random.seed(42)
    rows = []
    today = datetime.now()

    # For demo purposes, simulate 15 days of spending so the forecast looks realistic.
    # This gives the ML model enough data points to produce a convincing prediction.
    demo_days = max(today.day, 15)
    for day in range(1, demo_days + 1):
        try:
            date_str = today.replace(day=day).strftime("%Y-%m-%d")
        except ValueError:
            break
        n = random.choices([1, 2], weights=[60, 40])[0]
        for _ in range(n):
            cat  = random.choices(cat_names, weights=cat_weights)[0]
            info = daily_cats[cat]
            amt  = -round(random.uniform(*info["range"]), 2)
            rows.append({"date": date_str, "description": random.choice(info["vendors"]),
                         "category": cat, "currency": "CHF", "amount_original": amt, "amount": amt})

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date", ascending=False).reset_index(drop=True)


# ── LOAD DATA ─────────────────────────────────────────────────────────────────
# Try real database first, fall back to sample data if not ready yet
try:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from database.db_helper import get_expenses
    df_all = get_expenses()
    df_all["date"] = pd.to_datetime(df_all["date"])
    using_sample = False
except Exception:
    df_all = generate_sample_transactions()
    using_sample = True


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo + branding
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; padding:8px 0 16px;">
        <div style="background:#1A5C38; border-radius:12px; width:48px; height:48px;
                    display:flex; align-items:center; justify-content:center; flex-shrink:0;">
            <span style="color:white; font-size:1.5rem; font-weight:800; font-family:Inter,sans-serif;">w</span>
        </div>
        <div>
            <div style="font-weight:700; font-size:1rem; color:#1C2B2B;">UniWallet</div>
            <div style="font-size:.72rem; color:#5A6B6B;">University of St. Gallen</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation menu (visual only — not yet linked)
    st.markdown('<div style="font-size:.65rem; font-weight:700; text-transform:uppercase; letter-spacing:.1em; color:#5A6B6B; margin-bottom:6px;">MENU</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex; flex-direction:column; gap:4px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding:10px 12px; border-radius:8px; color:#5A6B6B; font-size:.88rem; font-weight:500;">
            <span>Dashboard</span>
            <span style="font-size:.7rem; background:#E8F5EE; color:#1A5C38; padding:2px 8px; border-radius:99px;">Soon</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding:10px 12px; border-radius:8px; color:#5A6B6B; font-size:.88rem; font-weight:500;">
            <span>Expense Log</span>
            <span style="font-size:.7rem; background:#E8F5EE; color:#1A5C38; padding:2px 8px; border-radius:99px;">Soon</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding:10px 12px; border-radius:8px; background:#E8F5EE; font-size:.88rem; font-weight:600; color:#1A5C38;
                    border-left:3px solid #1A5C38;">
            <span>Prediction</span>
        </div>
    </div>
    <hr style="border:none; border-top:1px solid #E8F5EE; margin:8px 0 16px;">
    """, unsafe_allow_html=True)

    monthly_budget = st.number_input("Monthly budget (CHF)", min_value=0.0, value=1200.0, step=50.0)
    today = datetime.now()
    month_options = []
    for i in range(6):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        month_options.append(f"{calendar.month_name[m]} {y}")
    selected_month_str = st.selectbox("Month", month_options)


# ── PAGE HEADER ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(120deg,#1A5C38 0%,#2A8A56 100%);
            border-radius:14px; padding:28px 36px; margin-bottom:1.5rem;
            display:flex; align-items:center; gap:24px;">
    <div style="background:rgba(255,255,255,0.15); border-radius:12px;
                width:56px; height:56px; display:flex; align-items:center;
                justify-content:center; flex-shrink:0; overflow:hidden;">
        <img src="app/static/logo.png" width="52"
             onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
             style="border-radius:10px;">
        <span style="font-size:1.5rem; font-weight:800; color:white; display:none;">W</span>
    </div>
    <div>
        <div style="font-size:1.4rem; font-weight:700; color:white; line-height:1.1; margin-bottom:2px;">
            UniWallet
        </div>
        <div style="font-size:1.4rem; font-weight:700; color:white; line-height:1.1; margin-bottom:6px;">
            Month-End Prediction
        </div>
        <div style="font-size:.88rem; color:rgba(255,255,255,0.8);">
            University of St. Gallen · Track, analyse, and forecast your student finances
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if using_sample:
    st.info("⚠️ Database not connected yet — showing sample data. Your page is working correctly!", icon="ℹ️")


# ── FILTER TO CURRENT MONTH EXPENSES ─────────────────────────────────────────
# Keep only negative amounts (expenses), make them positive for maths
month_start  = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
expenses_df  = df_all[df_all["amount_original"] < 0].copy()
expenses_df["amount"] = expenses_df["amount"].abs()
month_exp_df = expenses_df[expenses_df["date"] >= month_start].copy()

if len(month_exp_df) == 0:
    st.warning("No expenses recorded yet this month. Start logging to see your forecast!")
    st.stop()


# ── PREPARE TRAINING DATA ─────────────────────────────────────────────────────
# Group by day → cumulative spending. Model learns: day number → total spent.
daily_m = (month_exp_df.groupby(month_exp_df["date"].dt.date)["amount"]
           .sum().reset_index().sort_values("date"))
daily_m.columns = ["date", "total"]
daily_m["date"]       = pd.to_datetime(daily_m["date"])
daily_m["day"]        = daily_m["date"].dt.day
daily_m["cumulative"] = daily_m["total"].cumsum()

X = daily_m["day"].values.reshape(-1, 1)  # scikit-learn needs 2D array
y = daily_m["cumulative"].values

days_in_month  = calendar.monthrange(today.year, today.month)[1]
days_remaining = days_in_month - today.day
spent_so_far   = float(y[-1]) if len(y) > 0 else 0.0
avg_daily      = spent_so_far / today.day if today.day > 0 else 0.0


# ── LINEAR REGRESSION (scikit-learn) ─────────────────────────────────────────
# Train on days so far, predict total by end of month
if len(X) >= 2:
    model = LinearRegression()
    model.fit(X, y)
    projected_total   = float(model.predict([[days_in_month]])[0])
    projected_total   = max(projected_total, spent_so_far)
    future_days_range = list(range(today.day, days_in_month + 1))
    future_cumul      = [float(model.predict([[d]])[0]) for d in future_days_range]
else:
    projected_total   = avg_daily * days_in_month
    future_days_range = list(range(today.day, days_in_month + 1))
    future_cumul      = [avg_daily * d for d in future_days_range]

under_budget = projected_total <= monthly_budget
difference   = abs(monthly_budget - projected_total)


# ── FORECAST BANNER + CHART ───────────────────────────────────────────────────
left_col, right_col = st.columns([1, 2])

with left_col:
    # Green = under budget, red = over budget
    banner_class = "forecast-banner" if under_budget else "forecast-banner over-budget"
    status_line  = f"✅ CHF {difference:,.2f} under your CHF {monthly_budget:,.0f} budget" \
                   if under_budget else \
                   f"⚠️ CHF {difference:,.2f} over your CHF {monthly_budget:,.0f} budget"

    # Progress bar inside the banner
    progress_pct = min(spent_so_far / monthly_budget, 1.0) if monthly_budget > 0 else 0
    daily_remaining = (monthly_budget - spent_so_far) / days_remaining if days_remaining > 0 else 0

    st.markdown(f"""
    <div class="{banner_class}">
        <div class="fb-label">Projected Total · {selected_month_str}</div>
        <div class="fb-value">CHF {projected_total:,.2f}</div>
        <div class="fb-status">{status_line}</div>
        <div class="fb-note">{days_remaining} days remaining · avg CHF {avg_daily:.2f}/day</div>
        <div class="progress-wrap">
            <div class="progress-fill" style="width:{progress_pct*100:.1f}%;"></div>
        </div>
        <div class="progress-label">CHF {spent_so_far:,.2f} of CHF {monthly_budget:,.0f} used ({progress_pct*100:.1f}%)</div>
    </div>
    """, unsafe_allow_html=True)

    # Tip box below banner
    st.markdown(f"""
    <div class="tip-box">
        💡 To stay within budget, aim to spend at most
        <strong>CHF {daily_remaining:,.2f}/day</strong> for the rest of the month.
    </div>
    """, unsafe_allow_html=True)

with right_col:
    # Forecast chart: solid line = actual, dashed = forecast, red dotted = budget
    st.markdown('<div class="sec-header">Spending Forecast Chart</div>', unsafe_allow_html=True)

    fig = go.Figure()

    # Actual spending (solid green line with area fill)
    fig.add_trace(go.Scatter(
        x=daily_m["day"].tolist(), y=y.tolist(),
        mode="lines+markers", name="Actual spending",
        line=dict(color=GREEN_DARK, width=2.5),
        marker=dict(size=6, color=GREEN_DARK),
        fill="tozeroy", fillcolor="rgba(26,92,56,0.08)"
    ))

    # Forecast line (dashed, connects from last actual point to end of month)
    if future_days_range:
        conn_x = [daily_m["day"].iloc[-1]] + future_days_range
        conn_y = [spent_so_far] + future_cumul
        fig.add_trace(go.Scatter(
            x=conn_x, y=conn_y, mode="lines", name="Forecast",
            line=dict(color=GREEN_LIGHT, width=2.2, dash="dash")
        ))

    # Budget ceiling (red dotted horizontal line)
    fig.add_hline(
        y=monthly_budget, line_dash="dot", line_color="#C0392B",
        annotation_text=f"Budget: CHF {monthly_budget:,.0f}",
        annotation_position="top right", annotation_font_color="#C0392B"
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#111111", size=11),
        height=380, margin=dict(t=12, b=30, l=55, r=10),
        legend=dict(orientation="h", y=-0.2, font=dict(size=11, color="#111111")),
        xaxis=dict(showgrid=False, title="Day of month",
                   tickfont=dict(color="#111111"), title_font=dict(color="#111111")),
        yaxis=dict(showgrid=True, gridcolor="#E8F5EE", title="Cumulative spending (CHF)",
                   tickfont=dict(color="#111111"), title_font=dict(color="#111111")),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)


# ── KPI CARDS ROW ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">This Month at a Glance</div>', unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
cards = [
    (k1, "Spent So Far",    f"CHF {spent_so_far:,.2f}",    "pos"),
    (k2, "Projected Total", f"CHF {projected_total:,.2f}", "pos" if under_budget else "neg"),
    (k3, "Days Remaining",  f"{days_remaining} days",       "pos"),
    (k4, "Daily Average",   f"CHF {avg_daily:.2f}",         "pos"),
]
for col, label, value, cls in cards:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value {cls}">{value}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("UniWallet · Fundamentals & Methods of CS · University of St. Gallen · Spring 2026")