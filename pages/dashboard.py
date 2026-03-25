# =============================================================================
# UniWallet — Dashboard Page
# =============================================================================
# This file is ONE PAGE of a multi-page Streamlit web app.
# It shows the user an overview of their finances: balance, recent
# transactions, spending-by-category charts, and a monthly trend line.
#
# HOW TO RUN THIS FILE (in your Mac Terminal):
#   1. Open Terminal
#   2. Type:  pip install streamlit plotly pandas
#   3. Then:  streamlit run dashboard.py
#   A browser tab will open automatically with your dashboard.
# =============================================================================


# ── STEP 1: IMPORTS ──────────────────────────────────────────────────────────
# "Importing" means loading code that other people already wrote so we can
# use it.  Think of it like borrowing a toolbox instead of building your own.

import streamlit as st          # Streamlit turns this .py file into a web page
import pandas as pd             # Pandas helps us work with tables of data
import plotly.express as px     # Plotly draws interactive charts
import plotly.graph_objects as go  # Another Plotly module for advanced charts
from datetime import datetime, timedelta  # Helps us work with dates
import random                   # Lets us generate random sample data


# ── STEP 2: PAGE CONFIGURATION ──────────────────────────────────────────────
# st.set_page_config() MUST be the very first Streamlit command.
# It sets the browser tab title, the icon, and the layout width.

st.set_page_config(
    page_title="UniWallet — Dashboard",   # text shown on the browser tab
    page_icon="💰",                        # emoji shown on the browser tab
    layout="wide"                          # use the full width of the screen
)


# ── STEP 3: SAMPLE DATA ─────────────────────────────────────────────────────
# In the real app your teammates will load data from an API or a database.
# For now we CREATE fake (but realistic) data so you can build the visuals
# without waiting for the database to be ready.
#
# We wrap the data creation inside a FUNCTION decorated with @st.cache_data.
# This tells Streamlit: "Run this function once and remember the result.
# Don't re-create the data every time the user clicks something."

@st.cache_data                          # <-- decorator that caches the result
def generate_sample_transactions():
    """
    Create a pandas DataFrame with 90 days of fake transactions.
    Each row has: date, description, category, amount (negative = expense).
    """

    # These are the spending categories a student might have.
    categories = {
        "Food & Drinks":   ["Mensa HSG", "Migros", "Starbucks", "Döner Lade",
                            "Coop", "Uni Café"],
        "Transport":       ["SBB Ticket", "Lime Scooter", "Zurich HB Ticket"],
        "Entertainment":   ["Spotify", "Netflix", "Cinema Rex", "Book Store"],
        "Shopping":        ["Digitec", "H&M", "Amazon.de"],
        "Utilities":       ["Swisscom Mobile", "Health Insurance", "Rent"],
        "Education":       ["HSG Semester Fee", "Textbook", "Print Shop"],
    }

    # We will store each transaction as a dictionary in this list.
    transactions = []

    # Generate one transaction per day for the last 90 days.
    for i in range(90):
        # timedelta(days=i) means "i days".  We subtract it from today
        # to get a date in the past.
        date = datetime.now() - timedelta(days=i)

        # Pick a random category (e.g., "Food & Drinks")
        category = random.choice(list(categories.keys()))

        # Pick a random shop/description within that category
        description = random.choice(categories[category])

        # Generate a random expense amount between -5 and -120 CHF
        # (negative because it's money going OUT of the wallet)
        amount = -round(random.uniform(5, 120), 2)

        # Add the transaction to our list as a dictionary
        transactions.append({
            "date":        date.strftime("%Y-%m-%d"),   # e.g. "2026-03-15"
            "description": description,
            "category":    category,
            "amount":      amount
        })

    # Also sprinkle in some INCOME transactions (positive amounts)
    for i in range(0, 90, 30):   # every 30 days → roughly once a month
        date = datetime.now() - timedelta(days=i)
        transactions.append({
            "date":        date.strftime("%Y-%m-%d"),
            "description": "Monthly Allowance",
            "category":    "Income",
            "amount":      1500.00                      # positive = money IN
        })

    # Convert the list of dictionaries into a pandas DataFrame (a table).
    df = pd.DataFrame(transactions)

    # Make sure the "date" column is actually treated as a date type.
    df["date"] = pd.to_datetime(df["date"])

    # Sort so the newest transactions are on top.
    df = df.sort_values("date", ascending=False).reset_index(drop=True)

    return df   # return the finished table


# Call the function to get our data.
df = generate_sample_transactions()


# ── STEP 4: COMPUTE KEY NUMBERS ─────────────────────────────────────────────
# We calculate some headline numbers that we will display at the top of
# the dashboard in big "metric cards".

total_income   = df[df["amount"] > 0]["amount"].sum()
# ↑ Filter rows where amount > 0 (income), then sum them up.

total_expenses = df[df["amount"] < 0]["amount"].sum()
# ↑ Filter rows where amount < 0 (expenses), then sum them up.
#   This will be a negative number, e.g., -3200.50

current_balance = total_income + total_expenses
# ↑ Balance = income + expenses  (expenses are negative, so this works)

num_transactions = len(df)
# ↑ len() gives the number of rows → how many transactions we have


# ── STEP 5: CUSTOM STYLING (CSS) ────────────────────────────────────────────
# Streamlit lets you inject raw CSS to tweak how things look.
# st.markdown() with unsafe_allow_html=True writes raw HTML/CSS into the page.
# Don't worry about memorising CSS — just know that this block makes the
# metric cards and the page look nicer.

st.markdown("""
<style>
    /* Import a nicer font from Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

    /* Apply that font to everything on the page */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* Style for the metric cards at the top */
    .metric-card {
        background: linear-gradient(135deg, #1e1e2f 0%, #2d2d44 100%);
        border-radius: 16px;          /* rounded corners */
        padding: 24px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);   /* subtle shadow */
        transition: transform 0.2s;                  /* smooth hover */
    }
    .metric-card:hover {
        transform: translateY(-4px);   /* lift up on hover */
    }
    .metric-value {
        font-size: 2rem;              /* big number */
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.7;                 /* slightly faded */
        margin-bottom: 4px;
    }

    /* Give positive numbers a green colour */
    .positive { color: #4ade80; }
    /* Give negative numbers a red colour */
    .negative { color: #f87171; }

    /* Style the section headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
        color: #e2e8f0;
        border-left: 4px solid #6366f1;   /* purple left accent bar */
        padding-left: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ── STEP 6: PAGE HEADER ─────────────────────────────────────────────────────
# st.title() shows a big heading.
# st.caption() shows small grey text beneath it.

st.title("💰 UniWallet Dashboard")
st.caption("Your financial overview at a glance  •  University of St. Gallen")

# Add a thin horizontal line
st.divider()


# ── STEP 7: METRIC CARDS ROW ────────────────────────────────────────────────
# st.columns(4) creates 4 equal-width columns side by side.
# We put one metric card in each column.

col1, col2, col3, col4 = st.columns(4)

# --- Card 1: Current Balance ---
with col1:
    # f"..." is an f-string.  Anything inside {} gets replaced by its value.
    # :,.2f means: use commas as thousands separators, 2 decimal places.
    color_class = "positive" if current_balance >= 0 else "negative"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Current Balance</div>
        <div class="metric-value {color_class}">CHF {current_balance:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

# --- Card 2: Total Income ---
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Income (90 days)</div>
        <div class="metric-value positive">CHF {total_income:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

# --- Card 3: Total Expenses ---
with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Expenses (90 days)</div>
        <div class="metric-value negative">CHF {total_expenses:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

# --- Card 4: Number of Transactions ---
with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Transactions</div>
        <div class="metric-value">{num_transactions}</div>
    </div>
    """, unsafe_allow_html=True)


# ── STEP 8: SPENDING BY CATEGORY — DONUT CHART ──────────────────────────────
# We only want expenses (negative amounts) grouped by category.

st.markdown('<div class="section-header">Spending by Category</div>',
            unsafe_allow_html=True)

# Filter to expenses only, then take the absolute value so the chart
# shows positive numbers (nobody wants to see "negative food spending").
expenses_df = df[df["amount"] < 0].copy()           # keep only expenses
expenses_df["amount"] = expenses_df["amount"].abs()  # make positive

# Group by category and sum the amounts.
category_totals = (
    expenses_df
    .groupby("category")["amount"]   # group rows by category, look at amount
    .sum()                            # add up the amounts within each group
    .reset_index()                    # turn the result back into a normal table
)

# Create two columns: chart on the left, breakdown table on the right.
chart_col, table_col = st.columns([3, 2])  # 3:2 width ratio

with chart_col:
    # px.pie() creates a pie/donut chart.
    fig_donut = px.pie(
        category_totals,             # the data table
        values="amount",             # which column determines slice sizes
        names="category",            # which column provides the labels
        hole=0.5,                    # 0.5 = 50% hole in the middle → donut
        color_discrete_sequence=[    # custom colours for each slice
            "#6366f1", "#8b5cf6", "#a78bfa",
            "#c4b5fd", "#818cf8", "#4f46e5"
        ],
    )
    # Update the layout to remove the white background and resize.
    fig_donut.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",   # transparent background
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),       # light text colour
        height=380,
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(
            orientation="h",             # horizontal legend below chart
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    # st.plotly_chart() renders the interactive Plotly figure.
    st.plotly_chart(fig_donut, use_container_width=True)

with table_col:
    # Show the same data as a sorted table so users can read exact numbers.
    category_totals_sorted = category_totals.sort_values(
        "amount", ascending=False
    )
    # Rename columns for display
    display_table = category_totals_sorted.rename(columns={
        "category": "Category",
        "amount": "Total (CHF)"
    })
    # Round to 2 decimals
    display_table["Total (CHF)"] = display_table["Total (CHF)"].round(2)

    st.dataframe(
        display_table,
        use_container_width=True,
        hide_index=True               # don't show the row numbers
    )


# ── STEP 9: DAILY SPENDING TREND — LINE CHART ───────────────────────────────

st.markdown('<div class="section-header">Daily Spending Trend</div>',
            unsafe_allow_html=True)

# Group expenses by date and sum them.
daily_spending = (
    expenses_df
    .groupby("date")["amount"]
    .sum()
    .reset_index()
    .sort_values("date")
)

# Create a line chart with Plotly.
fig_line = px.area(
    daily_spending,
    x="date",
    y="amount",
    labels={"date": "Date", "amount": "Spending (CHF)"},
    color_discrete_sequence=["#6366f1"],   # purple line
)
fig_line.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e2e8f0"),
    height=350,
    margin=dict(t=20, b=40, l=40, r=20),
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
)

st.plotly_chart(fig_line, use_container_width=True)


# ── STEP 10: RECENT TRANSACTIONS TABLE ───────────────────────────────────────

st.markdown('<div class="section-header">Recent Transactions</div>',
            unsafe_allow_html=True)

# Let the user choose how many transactions to see with a slider.
# st.slider() creates a draggable slider widget.
num_to_show = st.slider(
    "Number of transactions to display",   # label shown above the slider
    min_value=5,                            # minimum value
    max_value=50,                           # maximum value
    value=15                                # default starting value
)

# Take the first `num_to_show` rows (data is already sorted newest first).
recent = df.head(num_to_show).copy()

# Format the amount column nicely: add "CHF" and colour.
recent["Amount (CHF)"] = recent["amount"].apply(
    lambda x: f"CHF {x:+,.2f}"      # + sign forces showing + or - sign
)

# Format the date to a readable string like "15 Mar 2026"
recent["Date"] = recent["date"].dt.strftime("%d %b %Y")

# Select and rename the columns we want to display.
display_recent = recent[["Date", "description", "category", "Amount (CHF)"]].rename(
    columns={
        "description": "Description",
        "category":    "Category"
    }
)

# Show the table.
st.dataframe(display_recent, use_container_width=True, hide_index=True)


# ── STEP 11: SIDEBAR FILTERS ────────────────────────────────────────────────
# The sidebar is the collapsible panel on the left side of a Streamlit app.
# We put filters here so the user can narrow down what they see.

with st.sidebar:
    st.header("🔍 Filters")
    st.caption("Use these to customise your dashboard view.")

    # Multi-select: the user can pick one or more categories.
    selected_categories = st.multiselect(
        "Categories",                                 # label
        options=df["category"].unique().tolist(),      # all unique categories
        default=df["category"].unique().tolist()       # start with all selected
    )

    # Date range picker
    date_range = st.date_input(
        "Date range",
        value=(df["date"].min().date(), df["date"].max().date()),
        min_value=df["date"].min().date(),
        max_value=df["date"].max().date()
    )

    st.divider()
    st.markdown("**UniWallet** v0.1")
    st.caption("Built with Streamlit for HSG FCS 2026")


# ── STEP 12: FOOTER ─────────────────────────────────────────────────────────

st.divider()
st.caption("UniWallet Dashboard  •  Fundamentals & Methods of CS  •  University of St. Gallen  •  Spring 2026")
