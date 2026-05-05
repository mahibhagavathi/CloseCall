import streamlit as st
import pandas as pd
import os
import time
import plotly.express as px
from groq import Groq
# =========================
# CONFIG
# =========================
st.set_page_config(page_title="CloseCall AI", layout="wide")

XLSX_PATH = "amazon_india_calls.xlsx"

client = OpenAI()

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
    df = df.rename(columns=COL_MAP)

    df["sentiment"] = df["sentiment_raw"].astype(str).str.strip().str.title()
    df["call_type"] = df["call_type_raw"].astype(str).str.strip().str.title()

    df["rep_score"] = df["csat"] if "csat" in df else 3

    return df


# =========================
# GPT SUMMARY
# =========================
@st.cache_data(show_spinner=False)
def generate_summary(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Summarize customer service calls in 1-2 concise lines."},
                {"role": "user", "content": text[:1000]}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Summary unavailable"


# =========================
# LOADING
# =========================
def render_loading():
    st.title("⚡ Analyzing Calls...")

    progress = st.progress(0)
    status = st.empty()

    steps = [
        "Reading transcripts",
        "Cleaning data",
        "Running AI summaries",
        "Building dashboard"
    ]

    for i, step in enumerate(steps):
        status.text(step)
        progress.progress((i + 1) / len(steps))
        time.sleep(0.3)

    df = load_data()

    # generate summaries (limit to avoid cost explosion)
    df["summary"] = df["content"].astype(str).apply(generate_summary)

    st.session_state["df"] = df
    st.session_state["stage"] = "dashboard"
    st.rerun()


# =========================
# KPIs
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

        fig1 = px.pie(sent, names="Sentiment", values="Count", title="Sentiment Distribution")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        agent_perf = df.groupby("agent_name")["rep_score"].mean().reset_index()

        fig2 = px.bar(agent_perf, x="agent_name", y="rep_score", title="Agent Performance")
        st.plotly_chart(fig2, use_container_width=True)


# =========================
# INSIGHTS + EMAIL
# =========================
def render_insights(df):
    st.subheader("🧠 AI Insights & Actions")

    if df.empty:
        st.info("No data")
        return

    total = len(df)
    negative_df = df[df["sentiment"] == "Negative"]

    top_issue = negative_df["product_category"].value_counts().idxmax() if not negative_df.empty else "None"
    worst_agent = df.groupby("agent_name")["rep_score"].mean().sort_values().index[0]

    st.markdown("### 🚨 Key Observations")
    st.markdown(f"- {len(negative_df)} out of {total} calls are negative")
    st.markdown(f"- Most complaints in **{top_issue}**")
    st.markdown(f"- Lowest performer: **{worst_agent}**")

    st.markdown("---")

    st.markdown("### 🎯 Next Actions")
    st.markdown(f"""
- Fix issues in **{top_issue}**
- Coach **{worst_agent}**
- Review negative transcripts
""")

    st.markdown("---")

    email = f"""
Subject: Customer Experience Issues Identified

Hi Team,

- {len(negative_df)} / {total} calls were negative
- Top issue: {top_issue}
- Low performer: {worst_agent}

Actions:
- Investigate category issues
- Agent coaching
- Transcript review

Best,
Insights Team
"""
    st.markdown("### 📧 Draft Email")
    st.code(email)


# =========================
# TABLE
# =========================
def render_table(df):
    st.subheader("📄 Calls")

    search = st.text_input("Search transcripts")

    if search:
        df = df[df["content"].str.contains(search, case=False, na=False)]

    clean = df[[
        "id",
        "agent_name",
        "product_category",
        "city",
        "state",
        "sentiment",
        "rep_score",
        "summary"
    ]]

    st.dataframe(clean, use_container_width=True)


# =========================
# DASHBOARD
# =========================
def render_dashboard():
    df = st.session_state["df"]

    st.title("📞 CloseCall AI — Call Intelligence")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        call_id = st.text_input("Call ID")

    with col2:
        category = st.selectbox("Product Category", ["All"] + sorted(df["product_category"].dropna().unique()))

    with col3:
        city = st.selectbox("City", ["All"] + sorted(df["city"].dropna().unique()))

    with col4:
        state = st.selectbox("State", ["All"] + sorted(df["state"].dropna().unique()))

    if call_id:
        df = df[df["id"].astype(str).str.contains(call_id)]

    if category != "All":
        df = df[df["product_category"] == category]

    if city != "All":
        df = df[df["city"] == city]

    if state != "All":
        df = df[df["state"] == state]

    st.markdown("---")
    render_kpis(df)

    st.markdown("---")
    render_charts(df)

    st.markdown("---")
    render_insights(df)

    st.markdown("---")
    render_table(df)


# =========================
# ROUTER
# =========================
if "stage" not in st.session_state:
    st.session_state["stage"] = "loading"

if st.session_state["stage"] == "loading":
    render_loading()
else:
    render_dashboard()
