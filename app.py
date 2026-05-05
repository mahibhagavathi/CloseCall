import streamlit as st
import pandas as pd
import os
import time
import plotly.express as px

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="CloseCall AI", layout="wide")

XLSX_PATH = "amazon_india_calls.xlsx"

# =========================
# COLUMN MAP
# =========================
COL_MAP = {
    "Call ID": "id",
    "Timestamp": "timestamp",
    "Duration (sec)": "duration_sec",
    "Hold Time (sec)": "hold_sec",
    "Channel": "channel",
    "Call Type": "call_type_raw",
    "Customer ID": "customer_id",
    "Customer Name": "customer_name",
    "Phone Number": "phone",
    "City": "city",
    "State": "state",
    "Country": "country",
    "Customer Service Agent": "agent_name",
    "Employee ID": "employee_id",
    "Agent Experience (Yrs)": "agent_exp_yrs",
    "Product ID": "product_id",
    "Product Name": "product_name",
    "Product Category": "product_category",
    "Sentiment": "sentiment_raw",
    "Resolution": "resolution_raw",
    "First Call Resolution": "fcr",
    "Transfers": "transfers",
    "CSAT Score (1-5)": "csat",
    "Transcript": "content",
}

# =========================
# DATA LOADER
# =========================
@st.cache_data(show_spinner=False)
def load_data():
    if not os.path.exists(XLSX_PATH):
        st.error(f"File not found: {XLSX_PATH}")
        st.stop()

    df = pd.read_excel(XLSX_PATH)

    # rename columns
    df = df.rename(columns=COL_MAP)

    # normalize sentiment
    df["sentiment"] = (
        df["sentiment_raw"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    # normalize call type
    df["call_type"] = (
        df["call_type_raw"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    # rep score (proxy using CSAT if exists)
    if "csat" in df.columns:
        df["rep_score"] = df["csat"]
    else:
        df["rep_score"] = 3

    return df


# =========================
# LOADING SCREEN
# =========================
def render_loading():
    st.title("⚡ Analyzing Calls...")

    progress = st.progress(0)
    status = st.empty()

    steps = [
        "Reading transcripts",
        "Cleaning data",
        "Analyzing sentiment",
        "Generating dashboard"
    ]

    for i, step in enumerate(steps):
        status.text(step)
        progress.progress((i + 1) / len(steps))
        time.sleep(0.3)

    df = load_data()

    st.session_state["df"] = df
    st.session_state["stage"] = "dashboard"
    st.rerun()


# =========================
# KPI SECTION
# =========================
def render_kpis(df):
    total = len(df)

    pos = len(df[df["sentiment"] == "Positive"])
    neg = len(df[df["sentiment"] == "Negative"])

    avg_score = df["rep_score"].mean()
    avg_duration = df["duration_sec"].mean()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("📞 Calls", total)
    c2.metric("😊 Positive %", f"{(pos/total*100):.1f}%" if total else "0%")
    c3.metric("😡 Negative %", f"{(neg/total*100):.1f}%" if total else "0%")
    c4.metric("⭐ Agent Score", f"{avg_score:.2f}")

    st.caption(f"⏱ Avg Duration: {int(avg_duration)} sec")


# =========================
# CHARTS
# =========================
def render_charts(df):
    col1, col2 = st.columns(2)

    with col1:
        sent = df["sentiment"].value_counts().reset_index()
        sent.columns = ["Sentiment", "Count"]

        fig1 = px.pie(
            sent,
            names="Sentiment",
            values="Count",
            title="Sentiment Distribution"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        agent_perf = df.groupby("agent_name")["rep_score"].mean().reset_index()

        fig2 = px.bar(
            agent_perf,
            x="agent_name",
            y="rep_score",
            title="Agent Performance"
        )
        st.plotly_chart(fig2, use_container_width=True)


# =========================
# TABLE
# =========================
def render_table(df):
    st.subheader("📄 Calls")

    search = st.text_input("Search transcripts")

    if search:
        df = df[df["content"].str.contains(search, case=False, na=False)]

    clean = df[[
        "timestamp",
        "agent_name",
        "call_type",
        "product_category",
        "sentiment",
        "rep_score",
        "duration_sec",
        "content"
    ]].copy()

    clean["content"] = clean["content"].astype(str).str[:100] + "..."

    st.dataframe(clean, use_container_width=True)


# =========================
# DASHBOARD
# =========================
def render_dashboard():
    df = st.session_state["df"]

    st.title("📞 CloseCall AI — Call Intelligence")

    # filters
    col1, col2, col3 = st.columns(3)

    with col1:
        sentiment = st.selectbox("Sentiment", ["All"] + sorted(df["sentiment"].dropna().unique()))

    with col2:
        call_type = st.selectbox("Call Type", ["All"] + sorted(df["call_type"].dropna().unique()))

    with col3:
        agent = st.selectbox("Agent", ["All"] + sorted(df["agent_name"].dropna().unique()))

    if sentiment != "All":
        df = df[df["sentiment"] == sentiment]

    if call_type != "All":
        df = df[df["call_type"] == call_type]

    if agent != "All":
        df = df[df["agent_name"] == agent]

    st.markdown("---")

    render_kpis(df)

    st.markdown("---")

    render_charts(df)

    st.markdown("---")

    render_table(df)


# =========================
# ROUTER
# =========================
if "stage" not in st.session_state:
    st.session_state["stage"] = "loading"

stage = st.session_state["stage"]

if stage == "loading":
    render_loading()
elif stage == "dashboard":
    render_dashboard()
