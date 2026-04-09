# =============================================================================
# UniWallet — Home Page
# University of St. Gallen  ·  Fundamentals & Methods of CS  ·  Spring 2026
# =============================================================================

import streamlit as st

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="UniWallet", page_icon="W", layout="wide")

# ── CSS (matches dashboard exactly) ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: #FFFFFF !important;
    color: #1C2B2B;
}

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

/* ── Sidebar logo ── */
.sb-logo { display:flex; align-items:center; gap:12px; padding-bottom:18px;
           border-bottom:1px solid #D1E7D9; margin-bottom:6px; }
.sb-logo-text .sb-name { font-size:1.15rem; font-weight:700; color:#1A5C38 !important; line-height:1.2; }
.sb-logo-text .sb-sub  { font-size:.68rem; color:#5A6B6B !important; letter-spacing:.03em; }

/* ── Page header ── */
.page-header {
    background: linear-gradient(120deg, #1A5C38 0%, #2A8A56 100%);
    border-radius: 14px; padding: 28px 36px; margin-bottom: 1.5rem;
}
.page-header h1 { font-size: 1.7rem; font-weight: 700; margin: 0; color: white !important; }
.page-header p  { margin: 6px 0 0; font-size: .88rem; opacity: .8; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR (identical to dashboard) ─────────────────────────────────────────
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
    st.caption("v0.1 · HSG · Spring 2026")

# ── PAGE CONTENT ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(120deg,#1A5C38 0%,#2A8A56 100%);
            border-radius:14px; padding:40px 36px; margin-bottom:1.5rem; text-align:center;">
    <div style="display:flex; align-items:center; justify-content:center; gap:18px; margin-bottom:12px;">
        <svg width="54" height="54" viewBox="0 0 54 54" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="lg" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#145232"/>
                    <stop offset="100%" stop-color="#2A8A56"/>
                </linearGradient>
            </defs>
            <rect width="54" height="54" rx="14" fill="url(#lg)"/>
            <polyline points="10,17 19,36 27,23 35,36 44,17"
                stroke="white" stroke-width="3.8" fill="none"
                stroke-linejoin="round" stroke-linecap="round"/>
            <circle cx="19" cy="36" r="2.8" fill="rgba(255,255,255,0.55)"/>
            <circle cx="35" cy="36" r="2.8" fill="rgba(255,255,255,0.55)"/>
            <line x1="10" y1="43" x2="44" y2="43"
                stroke="rgba(255,255,255,0.22)" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <h1 style="font-size:2.2rem; font-weight:700; color:white; margin:0;">UniWallet</h1>
    </div>
    <p style="font-size:1rem; color:rgba(255,255,255,0.85); margin:0;">
        Track, analyse, and forecast your student finances
    </p>
    <p style="font-size:.82rem; color:rgba(255,255,255,0.6); margin:8px 0 0;">
        University of St. Gallen · Fundamentals &amp; Methods of CS · Spring 2026
    </p>
</div>
""", unsafe_allow_html=True)

# ── CLICKABLE PAGE CARDS ─────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div style="background:white; border:1.5px solid #D1E7D9; border-radius:12px;
                padding:28px 24px; text-align:center; min-height:180px;">
        <div style="font-size:1.05rem; font-weight:700; color:#1A5C38; margin-bottom:6px;">Dashboard</div>
        <div style="font-size:.82rem; color:#5A6B6B; line-height:1.5;">
            Overview of your balance, spending breakdown, FX rates, and budget status.
        </div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/1_Dashboard.py", label="Open Dashboard")

with c2:
    st.markdown("""
    <div style="background:white; border:1.5px solid #D1E7D9; border-radius:12px;
                padding:28px 24px; text-align:center; min-height:180px;">
        <div style="font-size:1.05rem; font-weight:700; color:#1A5C38; margin-bottom:6px;">Prediction</div>
        <div style="font-size:.82rem; color:#5A6B6B; line-height:1.5;">
            ML-powered month-end spending forecast using Linear Regression.
        </div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/2_Prediction.py", label="Open Prediction")

with c3:
    st.markdown("""
    <div style="background:white; border:1.5px solid #D1E7D9; border-radius:12px;
                padding:28px 24px; text-align:center; min-height:180px;">
        <div style="font-size:1.05rem; font-weight:700; color:#1A5C38; margin-bottom:6px;">Expense Log</div>
        <div style="font-size:.82rem; color:#5A6B6B; line-height:1.5;">
            Add, edit, delete, and export your transactions with a real SQLite database.
        </div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/3_Expense_Log.py", label="Open Expense Log")

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.divider()
st.caption("UniWallet · Fundamentals & Methods of CS · University of St. Gallen · Spring 2026")
