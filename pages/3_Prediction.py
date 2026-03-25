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
CHART_COLORS = ["#1A5C38", "#2A8A56", "#4DB87A", "#7FCF9F", "#B2E4C8", "#D5F0E2"]

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
.kpi-sub   { font-size: .72rem; color: #5A6B6B; margin-top: 5px; }
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
.forecast-banner {
    background: linear-gradient(135deg, #1A5C38 0%, #2A8A56 100%);
    border-radius: 14px; padding: 24px 28px; color: white; margin-bottom: 1rem;
}
.forecast-banner.over-budget {
    background: linear-gradient(135deg, #922B21 0%, #C0392B 100%);
}
.fb-label { font-size: .72rem; font-weight: 600; text-transform: uppercase;
            letter-spacing: .08em; opacity: .8; margin-bottom: 8px; }
.fb-value { font-size: 2.4rem; font-weight: 700; line-height: 1.1; margin-bottom: 8px; }
.fb-status { font-size: .88rem; opacity: .9; margin-bottom: 4px; }
.fb-note  { font-size: .78rem; opacity: .75; }
.progress-wrap {
    background: #E8F5EE; border-radius: 99px; height: 12px;
    overflow: hidden; margin: 8px 0 4px;
}
.progress-fill { height: 100%; border-radius: 99px; transition: width .4s ease; }
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
EUR_TO_CHF_DATA = 0.947  # static rate baked into sample data

@st.cache_data
def generate_sample_transactions() -> pd.DataFrame:
    """
    Generates 90 days of realistic sample transactions for an HSG student.
    Used as fallback when the SQLite database is not available.
    Returns a DataFrame with columns: date, description, category,
    currency, amount_original, amount (in CHF).
    """
    daily_cats = {
        "Food & Drinks":  {"vendors": ["Mensa HSG","Migros","Coop","Starbucks","Uni Café","Döner Laden"], "range": (6, 20),  "weight": 5},
        "Transport":      {"vendors": ["SBB Tageskarte","PostAuto","Lime Scooter"],                        "range": (4, 26),  "weight": 2},
        "Entertainment":  {"vendors": ["Cinema Scala","Bar 7","Netflix","Book Store"],                     "range": (9, 40),  "weight": 1},
        "Shopping":       {"vendors": ["Digitec","H&M","Zalando","IKEA Konstanz"],                         "range": (18, 75), "weight": 1},
        "Education":      {"vendors": ["Print Shop HSG","Textbook","Coursera"],                            "range": (5, 35),  "weight": 1},
    }
    cat_names   = list(daily_cats.keys())
    cat_weights = [daily_cats[c]["weight"] for c in cat_names]
    random.seed(7)
    rows = []

    # Variable daily spending (random categories, random amounts)
    for i in range(90):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        n = random.choices([0, 1, 2], weights=[15, 65, 20])[0]
        for _ in range(n):
            cat  = random.choices(cat_names, weights=cat_weights)[0]
            info = daily_cats[cat]
            amt  = -round(random.uniform(*info["range"]), 2)
            rows.append({"date": date_str, "description": random.choice(info["vendors"]),
                         "category": cat, "currency": "CHF", "amount_original": amt, "amount": amt})

    # Fixed monthly costs (rent, insurance, phone, Spotify)
    for i in range(0, 90, 30):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        for desc, amt in [("WG Miete", -780.00), ("Krankenkasse Prämie", -310.00),
                          ("Swisscom Mobile", -49.00), ("Spotify", -12.90)]:
            rows.append({"date": date_str, "description": desc, "category": "Utilities",
                         "currency": "CHF", "amount_original": amt, "amount": amt})

    # One-off semester fee
    rows.append({"date": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
                 "description": "HSG Semester Fee", "category": "Education",
                 "currency": "CHF", "amount_original": -650.00, "amount": -650.00})

    # Monthly income: EUR parental allowance + CHF part-time job
    for i in range(0, 90, 30):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        eur_orig = 1800.00
        rows.append({"date": date_str, "description": "Eltern Überweisung",
                     "category": "Income", "currency": "EUR",
                     "amount_original": eur_orig, "amount": round(eur_orig * EUR_TO_CHF_DATA, 2)})
        rows.append({"date": date_str, "description": "Studentenjob Lohn",
                     "category": "Income", "currency": "CHF",
                     "amount_original": 700.00, "amount": 700.00})

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date", ascending=False).reset_index(drop=True)


# ── LOAD DATA ─────────────────────────────────────────────────────────────────
# Try to load from the shared SQLite database via db_helper.py.
# If it's not available yet, fall back to sample data so the page still works.
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
    st.markdown("## 💳 UniWallet")
    st.markdown("---")

    # User sets their monthly budget here — used for colour-coding the forecast
    monthly_budget = st.number_input("Monthly budget (CHF)", min_value=0.0, value=1200.0, step=50.0)

    # Month selector — last 6 months available
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

    st.markdown("---")
    st.caption("📈 Prediction · UniWallet")


# ── PAGE HEADER ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
    <h1>📈 Month-End Prediction</h1>
    <p>ML-powered spending forecast · {selected_month_str}</p>
</div>
""", unsafe_allow_html=True)

# Show a notice if we're using sample data instead of the real database
if using_sample:
    st.info("⚠️ Database not connected yet — showing sample data. Your page is working correctly!", icon="ℹ️")


# ── FILTER DATA TO CURRENT MONTH EXPENSES ONLY ───────────────────────────────
# Keep only negative amounts (expenses), make them positive for easier maths
month_start  = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
expenses_df  = df_all[df_all["amount_original"] < 0].copy()
expenses_df["amount"] = expenses_df["amount"].abs()
month_exp_df = expenses_df[expenses_df["date"] >= month_start].copy()

# If no data exists yet, stop here with a friendly message
if len(month_exp_df) == 0:
    st.warning("No expenses recorded yet this month. Start logging to see your forecast!")
    st.stop()


# ── PREPARE TRAINING DATA FOR ML MODEL ───────────────────────────────────────
# Group expenses by day to get daily totals, then compute cumulative spending.
# The ML model learns from: day number → cumulative spending so far.
daily_m = (month_exp_df.groupby(month_exp_df["date"].dt.date)["amount"]
           .sum().reset_index().sort_values("date"))
daily_m.columns = ["date", "total"]
daily_m["date"]       = pd.to_datetime(daily_m["date"])
daily_m["day"]        = daily_m["date"].dt.day       # day number (1–31)
daily_m["cumulative"] = daily_m["total"].cumsum()    # running total


# ── LINEAR REGRESSION MODEL (scikit-learn) ────────────────────────────────────
# X = day number (e.g. 1, 2, 3 ... up to today)
# y = cumulative spending on that day
# We train on data so far, then predict cumulative spending on the last day of the month.
X = daily_m["day"].values.reshape(-1, 1)  # scikit-learn needs a 2D array
y = daily_m["cumulative"].values

days_in_month  = calendar.monthrange(today.year, today.month)[1]
days_remaining = days_in_month - today.day
spent_so_far   = float(y[-1]) if len(y) > 0 else 0.0
avg_daily      = spent_so_far / today.day if today.day > 0 else 0.0

if len(X) >= 2:
    # Train the Linear Regression model
    model = LinearRegression()
    model.fit(X, y)

    # Predict spending on the last day of the month
    projected_total = float(model.predict([[days_in_month]])[0])

    # Spending can't decrease — floor at what's already been spent
    projected_total = max(projected_total, spent_so_far)

    # Generate forecast values for every future day (for the chart)
    future_days_range = list(range(today.day, days_in_month + 1))
    future_cumul = [float(model.predict([[d]])[0]) for d in future_days_range]

else:
    # Not enough data points — fall back to simple daily average extrapolation
    projected_total   = avg_daily * days_in_month
    future_days_range = list(range(today.day, days_in_month + 1))
    future_cumul      = [avg_daily * d for d in future_days_range]

# Determine if user is on track or over budget
under_budget = projected_total <= monthly_budget
difference   = abs(monthly_budget - projected_total)


# ── FORECAST BANNER + CHART (side by side) ───────────────────────────────────
left_col, right_col = st.columns([1, 2])

with left_col:
    # Green banner = under budget, red banner = over budget
    banner_class = "forecast-banner" if under_budget else "forecast-banner over-budget"
    status_line  = f"✅ CHF {difference:,.2f} under your CHF {monthly_budget:,.0f} budget" \
                   if under_budget else \
                   f"⚠️ CHF {difference:,.2f} over your CHF {monthly_budget:,.0f} budget"

    st.markdown(f"""
    <div class="{banner_class}">
        <div class="fb-label">Projected Total · {selected_month_str}</div>
        <div class="fb-value">CHF {projected_total:,.2f}</div>
        <div class="fb-status">{status_line}</div>
        <div class="fb-note">{days_remaining} days remaining · avg CHF {avg_daily:.2f}/day</div>
    </div>
    """, unsafe_allow_html=True)

    # Budget progress bar — colour changes: green → amber → red
    progress_pct = min(spent_so_far / monthly_budget, 1.0) if monthly_budget > 0 else 0
    bar_color    = GREEN_MID if progress_pct < 0.75 else ("#E67E22" if progress_pct < 1.0 else "#C0392B")
    st.markdown(f"""
    <div style="font-size:.72rem; font-weight:600; text-transform:uppercase;
                letter-spacing:.08em; color:#5A6B6B; margin-top:.5rem;">Budget used so far</div>
    <div class="progress-wrap">
        <div class="progress-fill" style="width:{progress_pct*100:.1f}%; background:{bar_color};"></div>
    </div>
    <div style="font-size:.75rem; color:#5A6B6B;">
        CHF {spent_so_far:,.2f} of CHF {monthly_budget:,.0f} ({progress_pct*100:.1f}%)
    </div>
    """, unsafe_allow_html=True)

    # Tip: how much the user can spend per day to stay within budget
    daily_remaining = (monthly_budget - spent_so_far) / days_remaining if days_remaining > 0 else 0
    st.markdown(f"""
    <div class="tip-box">
        💡 To stay within budget, aim to spend at most
        <strong>CHF {daily_remaining:,.2f}/day</strong> for the rest of the month.
    </div>
    """, unsafe_allow_html=True)

with right_col:
    # Solid line = actual spending so far
    # Dashed line = model's forecast for the remaining days
    # Red dotted line = budget ceiling
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
        height=300, margin=dict(t=12, b=30, l=55, r=10),
        legend=dict(orientation="h", y=-0.28, font=dict(size=11, color="#111111")),
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


# ── SPENDING BY CATEGORY ──────────────────────────────────────────────────────
# Shows a donut chart and category progress bars for this month's spending
st.markdown('<div class="sec-header">Spending by Category This Month</div>', unsafe_allow_html=True)

cat_left, cat_right = st.columns([1, 1])

# Group spending by category
cat_totals = (month_exp_df.groupby("category")["amount"]
              .sum().sort_values(ascending=False).reset_index())
cat_totals.columns = ["Category", "Total"]

with cat_left:
    # Donut chart — quick visual breakdown by category
    fig_pie = go.Figure(go.Pie(
        labels=cat_totals["Category"], values=cat_totals["Total"],
        hole=0.45, marker_colors=CHART_COLORS,
        textfont=dict(family="Inter", size=11),
    ))
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", height=280,
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", y=-0.15, font=dict(size=10, color="#111111")),
        font=dict(family="Inter", color="#111111"),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with cat_right:
    # Horizontal progress bars — shows each category's share of total spending
    max_amt   = cat_totals["Total"].max() if len(cat_totals) else 1
    rows_html = ""
    for _, row in cat_totals.iterrows():
        bar_pct = row["Total"] / max_amt * 100
        rows_html += f"""
        <div style="margin-bottom:10px;">
          <div style="display:flex; justify-content:space-between; font-size:.78rem;
                      margin-bottom:4px; color:#1C2B2B;">
            <span style="font-weight:500;">{row['Category']}</span>
            <span style="color:#5A6B6B; font-weight:600;">CHF {row['Total']:,.2f}</span>
          </div>
          <div style="height:6px; background:#E8F5EE; border-radius:99px; overflow:hidden;">
            <div style="width:{bar_pct:.1f}%; height:100%; background:#2A8A56; border-radius:99px;"></div>
          </div>
        </div>"""
    st.markdown(
        f'<div style="background:white; border:1.5px solid #D1E7D9; border-radius:12px; '
        f'padding:16px 18px; margin-top:8px;">{rows_html}</div>',
        unsafe_allow_html=True
    )


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("UniWallet · Fundamentals & Methods of CS · University of St. Gallen · Spring 2026")