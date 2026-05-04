import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_all_transcripts
from analyzer import analyze_batch, analyze_transcript

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Call Intelligence",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #0a0a0f;
    color: #e8e8f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f0f18 !important;
    border-right: 1px solid #1e1e2e;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #6b6b8a;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-family: 'DM Mono', monospace;
}

/* Header */
.main-header {
    padding: 2rem 0 1.5rem 0;
    border-bottom: 1px solid #1e1e2e;
    margin-bottom: 2rem;
}
.main-title {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2.4rem;
    color: #ffffff;
    letter-spacing: -0.02em;
    line-height: 1;
}
.main-subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: #4ade80;
    letter-spacing: 0.08em;
    margin-top: 0.4rem;
    text-transform: uppercase;
}

/* KPI Cards */
.kpi-card {
    background: #0f0f18;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    transition: border-color 0.2s;
}
.kpi-card:hover { border-color: #4ade80; }
.kpi-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #6b6b8a;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 2rem;
    color: #ffffff;
    line-height: 1;
}
.kpi-sub {
    font-size: 0.75rem;
    color: #4ade80;
    margin-top: 0.3rem;
    font-family: 'DM Mono', monospace;
}

/* Section headers */
.section-title {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
    color: #ffffff;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e1e2e;
}

/* Quote card */
.quote-card {
    background: #0f0f18;
    border-left: 3px solid #4ade80;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    font-style: italic;
    color: #c8c8e0;
    font-size: 0.9rem;
}

/* Transcript viewer */
.transcript-box {
    background: #0f0f18;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    color: #a0a0c0;
    line-height: 1.8;
    max-height: 400px;
    overflow-y: auto;
}

/* Score badge */
.score-badge {
    display: inline-block;
    background: #1a2e1a;
    color: #4ade80;
    border: 1px solid #4ade80;
    border-radius: 20px;
    padding: 2px 12px;
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    font-weight: 500;
}

/* Tag badges */
.tag {
    display: inline-block;
    border-radius: 4px;
    padding: 2px 10px;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 500;
    margin-right: 4px;
}
.tag-positive  { background: #1a2e1a; color: #4ade80; border: 1px solid #4ade8040; }
.tag-negative  { background: #2e1a1a; color: #f87171; border: 1px solid #f8717140; }
.tag-neutral   { background: #1e1e2e; color: #a0a0c0; border: 1px solid #a0a0c040; }
.tag-mixed     { background: #2e2a1a; color: #fbbf24; border: 1px solid #fbbf2440; }

/* Streamlit overrides */
.stButton > button {
    background: #4ade80 !important;
    color: #0a0a0f !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1.5rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

div[data-testid="stSelectbox"] label,
div[data-testid="stMultiSelect"] label {
    color: #6b6b8a !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    color: #6b6b8a !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
.stTabs [aria-selected="true"] {
    color: #4ade80 !important;
    border-bottom-color: #4ade80 !important;
}

div[data-testid="stTextArea"] textarea {
    background: #0f0f18 !important;
    border: 1px solid #1e1e2e !important;
    color: #e8e8f0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
    border-radius: 8px !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid #1e1e2e !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

.stProgress > div > div {
    background-color: #4ade80 !important;
}

.stSpinner > div {
    border-top-color: #4ade80 !important;
}

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Plotly theme ───────────────────────────────────────────────────────────────
PLOT_BG = "#0a0a0f"
PAPER_BG = "#0f0f18"
GRID_COLOR = "#1e1e2e"
TEXT_COLOR = "#a0a0c0"
ACCENT = "#4ade80"
PALETTE = ["#4ade80", "#60a5fa", "#f59e0b", "#f87171", "#a78bfa", "#34d399", "#fb923c"]

def style_fig(fig):
    fig.update_layout(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(family="DM Mono, monospace", color=TEXT_COLOR, size=11),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            bgcolor="#0f0f18",
            bordercolor="#1e1e2e",
            borderwidth=1,
            font=dict(size=10)
        )
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR)
    return fig


# ── Session state ──────────────────────────────────────────────────────────────
if "results_df" not in st.session_state:
    st.session_state.results_df = None
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📞 Sales Intelligence")
    st.markdown("---")
    st.markdown("**FILTERS**")

    company_filter = []
    sentiment_filter = []
    outcome_filter = []

    if st.session_state.results_df is not None:
        df = st.session_state.results_df
        companies = sorted(df["company"].unique().tolist())
        company_filter = st.multiselect("Company", companies, default=companies)

        sentiments = sorted(df["sentiment"].unique().tolist())
        sentiment_filter = st.multiselect("Sentiment", sentiments, default=sentiments)

        outcomes = sorted(df["outcome"].unique().tolist())
        outcome_filter = st.multiselect("Outcome", outcomes, default=outcomes)

    st.markdown("---")
    st.markdown("**DATASET**")
    st.markdown("Source: HuggingFace\ngwenshap/sales-transcripts")
    st.markdown("**MODEL**")
    st.markdown("Groq · LLaMA 3.3 70B")


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <div class="main-title">Sales Call Intelligence</div>
    <div class="main-subtitle">◆ AI-Powered Transcript Analysis Agent</div>
</div>
""", unsafe_allow_html=True)


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["DASHBOARD", "TRANSCRIPTS", "SINGLE ANALYSIS"])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    if not st.session_state.analyzed:
        st.markdown("""
        <div style="text-align:center; padding: 4rem 2rem;">
            <div style="font-family:'Syne',sans-serif; font-size:1.5rem; color:#fff; margin-bottom:1rem;">
                Ready to analyze 103 sales transcripts
            </div>
            <div style="font-family:'DM Mono',monospace; font-size:0.8rem; color:#6b6b8a; margin-bottom:2rem;">
                Groq LLaMA 3.3 will extract sentiment, call type, resolution status, rep scores and more
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_btn = st.columns([1, 2, 1])[1]
        with col_btn:
            if st.button("⚡ Run Analysis on All Transcripts"):
                with st.spinner("Fetching transcripts from HuggingFace..."):
                    transcripts = load_all_transcripts()

                progress = st.progress(0, text="Starting analysis...")
                results = analyze_batch(transcripts, progress_bar=progress)
                progress.empty()

                st.session_state.results_df = pd.DataFrame(results)
                st.session_state.analyzed = True
                st.rerun()
    else:
        df_all = st.session_state.results_df.copy()

        # Apply filters
        if company_filter:
            df = df_all[df_all["company"].isin(company_filter)]
        else:
            df = df_all
        if sentiment_filter:
            df = df[df["sentiment"].isin(sentiment_filter)]
        if outcome_filter:
            df = df[df["outcome"].isin(outcome_filter)]

        # ── KPI row ──────────────────────────────────────────────────────────
        total = len(df)
        resolved_pct = round(len(df[df["resolution_status"] == "Resolved"]) / total * 100) if total else 0
        avg_score = round(df["rep_score"].mean(), 1) if total else 0
        sale_likely = len(df[df["outcome"] == "Sale Likely"])
        positive_pct = round(len(df[df["sentiment"] == "Positive"]) / total * 100) if total else 0

        k1, k2, k3, k4, k5 = st.columns(5)
        kpis = [
            (k1, "Calls Analyzed", str(total), "transcripts"),
            (k2, "Resolution Rate", f"{resolved_pct}%", "calls resolved"),
            (k3, "Avg Rep Score", f"{avg_score}/5", "performance rating"),
            (k4, "Sale Likely", str(sale_likely), f"{round(sale_likely/total*100)}% of calls" if total else "—"),
            (k5, "Positive Sentiment", f"{positive_pct}%", "happy customers"),
        ]
        for col, label, value, sub in kpis:
            with col:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-sub">{sub}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 1: Sentiment + Call Type ──────────────────────────────────────
        c1, c2 = st.columns(2)

        with c1:
            st.markdown('<div class="section-title">Sentiment Distribution</div>', unsafe_allow_html=True)
            sent_counts = df["sentiment"].value_counts().reset_index()
            sent_counts.columns = ["sentiment", "count"]
            colors = {"Positive": "#4ade80", "Negative": "#f87171", "Neutral": "#60a5fa", "Mixed": "#fbbf24"}
            fig_sent = px.pie(
                sent_counts, values="count", names="sentiment",
                color="sentiment",
                color_discrete_map=colors,
                hole=0.55
            )
            fig_sent.update_traces(textfont_size=11, textfont_color="#fff")
            fig_sent = style_fig(fig_sent)
            st.plotly_chart(fig_sent, use_container_width=True)

        with c2:
            st.markdown('<div class="section-title">Call Type Breakdown</div>', unsafe_allow_html=True)
            type_counts = df["call_type"].value_counts().reset_index()
            type_counts.columns = ["type", "count"]
            fig_type = px.bar(
                type_counts, x="count", y="type", orientation="h",
                color="count", color_continuous_scale=["#1a3a2a", "#4ade80"]
            )
            fig_type.update_layout(coloraxis_showscale=False, yaxis_title=None, xaxis_title=None)
            fig_type = style_fig(fig_type)
            st.plotly_chart(fig_type, use_container_width=True)

        # ── Row 2: Resolution + Outcome ───────────────────────────────────────
        c3, c4 = st.columns(2)

        with c3:
            st.markdown('<div class="section-title">Resolution Status</div>', unsafe_allow_html=True)
            res_counts = df["resolution_status"].value_counts().reset_index()
            res_counts.columns = ["status", "count"]
            res_colors = {"Resolved": "#4ade80", "Unresolved": "#f87171", "Escalated": "#fbbf24", "Pending": "#60a5fa"}
            fig_res = px.bar(
                res_counts, x="status", y="count",
                color="status", color_discrete_map=res_colors
            )
            fig_res.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
            fig_res = style_fig(fig_res)
            st.plotly_chart(fig_res, use_container_width=True)

        with c4:
            st.markdown('<div class="section-title">Sales Outcome</div>', unsafe_allow_html=True)
            out_counts = df["outcome"].value_counts().reset_index()
            out_counts.columns = ["outcome", "count"]
            out_colors = {
                "Sale Likely": "#4ade80", "Sale Unlikely": "#f87171",
                "Neutral": "#60a5fa", "Follow-up Needed": "#fbbf24"
            }
            fig_out = px.pie(
                out_counts, values="count", names="outcome",
                color="outcome", color_discrete_map=out_colors,
                hole=0.55
            )
            fig_out.update_traces(textfont_size=11, textfont_color="#fff")
            fig_out = style_fig(fig_out)
            st.plotly_chart(fig_out, use_container_width=True)

        # ── Row 3: Rep Score by Company ───────────────────────────────────────
        st.markdown('<div class="section-title">Avg Rep Score by Company</div>', unsafe_allow_html=True)
        company_scores = df.groupby("company")["rep_score"].mean().reset_index()
        company_scores.columns = ["company", "avg_score"]
        company_scores = company_scores.sort_values("avg_score", ascending=True)
        fig_cs = px.bar(
            company_scores, x="avg_score", y="company", orientation="h",
            color="avg_score", color_continuous_scale=["#f87171", "#fbbf24", "#4ade80"],
            range_color=[1, 5]
        )
        fig_cs.update_layout(coloraxis_showscale=False, xaxis_range=[0, 5], yaxis_title=None, xaxis_title="Average Score (1–5)")
        fig_cs = style_fig(fig_cs)
        st.plotly_chart(fig_cs, use_container_width=True)

        # ── Top Objections ────────────────────────────────────────────────────
        st.markdown('<div class="section-title">Common Objections</div>', unsafe_allow_html=True)
        objections = df[df["top_objection"].notna() & (df["top_objection"] != "None")]["top_objection"].tolist()
        if objections:
            for obj in objections[:6]:
                st.markdown(f'<div class="quote-card">"{obj}"</div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#6b6b8a;">No objections found in filtered data.</p>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Re-run Analysis"):
            st.session_state.results_df = None
            st.session_state.analyzed = False
            st.cache_data.clear()
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — TRANSCRIPTS TABLE
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    if st.session_state.results_df is None:
        st.info("Run the analysis first in the Dashboard tab.")
    else:
        df_all = st.session_state.results_df.copy()
        if company_filter:
            df_view = df_all[df_all["company"].isin(company_filter)]
        else:
            df_view = df_all
        if sentiment_filter:
            df_view = df_view[df_view["sentiment"].isin(sentiment_filter)]
        if outcome_filter:
            df_view = df_view[df_view["outcome"].isin(outcome_filter)]

        st.markdown(f'<div class="section-title">All Transcripts — {len(df_view)} results</div>', unsafe_allow_html=True)

        display_cols = ["id", "company", "sentiment", "call_type", "resolution_status", "outcome", "rep_score", "key_issue"]
        st.dataframe(
            df_view[display_cols].rename(columns={
                "id": "Call", "company": "Company", "sentiment": "Sentiment",
                "call_type": "Type", "resolution_status": "Resolution",
                "outcome": "Outcome", "rep_score": "Rep Score", "key_issue": "Key Issue"
            }),
            use_container_width=True,
            height=500
        )

        st.markdown('<div class="section-title" style="margin-top:2rem;">Transcript Detail</div>', unsafe_allow_html=True)
        selected = st.selectbox("Select a transcript to inspect", df_view["id"].tolist())
        row = df_view[df_view["id"] == selected].iloc[0]

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Sentiment", row["sentiment"])
        d2.metric("Rep Score", f"{row['rep_score']}/5")
        d3.metric("Resolution", row["resolution_status"])
        d4.metric("Outcome", row["outcome"])

        st.markdown(f'<div class="quote-card">💬 {row["standout_quote"]}</div>', unsafe_allow_html=True)
        st.markdown(f"**Sentiment arc:** {row['sentiment_arc']}")
        st.markdown(f"**Rep feedback:** {row['rep_score_reason']}")

        with st.expander("View full transcript"):
            st.markdown(f'<div class="transcript-box">{row["content"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — SINGLE ANALYSIS
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-title">Paste Any Transcript for Instant Analysis</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#6b6b8a; font-size:0.85rem; font-family:\'DM Mono\',monospace; margin-bottom:1rem;">Great for demos — paste any sales call transcript and get results in seconds.</p>', unsafe_allow_html=True)

    sample = """Sales Rep: Hi, thanks for calling. How can I help you today?
Customer: I've been trying to get a refund for 2 weeks and nobody is helping me.
Sales Rep: I'm really sorry to hear that. Let me pull up your account right now.
Customer: This is ridiculous, I just want my money back.
Sales Rep: I completely understand your frustration. I can see your case here. I'm going to escalate this to our billing team immediately and ensure you get a resolution within 24 hours.
Customer: Finally. That's all I wanted.
Sales Rep: Again, I apologize for the delay. You'll get an email confirmation within the hour."""

    transcript_input = st.text_area(
        "Paste transcript here",
        value=sample,
        height=260,
        placeholder="Sales Rep: ...\nCustomer: ..."
    )

    if st.button("🔍 Analyze This Transcript"):
        with st.spinner("Analyzing with Groq LLaMA..."):
            result = analyze_transcript(transcript_input, "manual_input")

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Sentiment", result.get("sentiment", "—"))
        r2.metric("Call Type", result.get("call_type", "—"))
        r3.metric("Resolution", result.get("resolution_status", "—"))
        r4.metric("Rep Score", f"{result.get('rep_score', '—')}/5")

        st.markdown("<br>", unsafe_allow_html=True)
        c_l, c_r = st.columns(2)

        with c_l:
            st.markdown("**Sentiment Arc**")
            st.markdown(f'<div class="quote-card">{result.get("sentiment_arc", "—")}</div>', unsafe_allow_html=True)
            st.markdown("**Key Issue**")
            st.markdown(f'<div class="quote-card">{result.get("key_issue", "—")}</div>', unsafe_allow_html=True)
            st.markdown("**Top Objection**")
            st.markdown(f'<div class="quote-card">{result.get("top_objection", "—")}</div>', unsafe_allow_html=True)

        with c_r:
            st.markdown("**Sales Outcome**")
            st.markdown(f'<div class="quote-card">{result.get("outcome", "—")}</div>', unsafe_allow_html=True)
            st.markdown("**Rep Performance**")
            st.markdown(f'<div class="quote-card">{result.get("rep_score_reason", "—")}</div>', unsafe_allow_html=True)
            st.markdown("**Standout Quote**")
            st.markdown(f'<div class="quote-card">"{result.get("standout_quote", "—")}"</div>', unsafe_allow_html=True)
