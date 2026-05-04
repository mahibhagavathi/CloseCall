
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_sample_transcripts, load_csv_transcripts
from analyzer import analyze_batch, generate_email

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CloseCall — Sales Intelligence",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg":           "#f0f4f8",
    "surface":      "#ffffff",
    "border":       "#dde3ec",
    "sidebar_bg":   "#1c2333",
    "sidebar_text": "#a8b4c8",
    "sidebar_head": "#ffffff",
    "text_primary": "#0f1923",
    "text_secondary":"#4a5568",
    "text_muted":   "#8896a8",
    "accent":       "#0ea5e9",       # sky-500
    "accent_dk":    "#0284c7",
    "accent_light": "#e0f2fe",
    "positive":     "#059669",
    "positive_bg":  "#ecfdf5",
    "negative":     "#dc2626",
    "negative_bg":  "#fef2f2",
    "mixed":        "#d97706",
    "mixed_bg":     "#fffbeb",
    "neutral_bg":   "#f1f5f9",
    "hot":          "#dc2626",
    "hot_bg":       "#fef2f2",
    "warm":         "#d97706",
    "warm_bg":      "#fffbeb",
    "cold":         "#2563eb",
    "cold_bg":      "#eff6ff",
}

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

*, html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}}
.stApp {{ background: {C['bg']}; }}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: {C['sidebar_bg']} !important;
    border-right: none !important;
}}
[data-testid="stSidebar"] * {{ color: {C['sidebar_text']} !important; }}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{ color: {C['sidebar_head']} !important; }}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label {{
    color: {C['sidebar_text']} !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    font-weight: 600 !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] div {{
    background: #253048 !important;
    border-color: #3a4a63 !important;
    color: #ffffff !important;
}}
[data-testid="stSidebar"] [data-baseweb="tag"] {{
    background: #0ea5e9 !important;
}}

/* ── Hide chrome ── */
#MainMenu, footer, header {{ visibility: hidden; }}
[data-testid="stToolbar"] {{ display: none; }}

/* ── Progress bar & text ── */
.stProgress > div > div {{ background-color: {C['accent']} !important; }}
.stProgress p, [data-testid="stProgressBarText"],
div[class*="progress"] p {{ color: {C['text_primary']} !important; font-size: 0.85rem !important; font-weight: 600 !important; }}

/* ── Logo ── */
.logo {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 2.6rem;
    letter-spacing: -0.03em;
    line-height: 1;
    color: {C['text_primary']};
}}
.logo span {{ color: {C['accent']}; }}
.logo-sub {{
    font-size: 0.72rem;
    font-weight: 600;
    color: {C['text_muted']};
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 0.3rem;
}}

/* ── KPI Cards ── */
.kpi-card {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 14px;
    padding: 1.5rem 1.8rem;
    border-top: 3px solid {C['accent']};
}}
.kpi-label {{
    font-size: 0.72rem;
    font-weight: 700;
    color: {C['text_muted']};
    text-transform: uppercase;
    letter-spacing: 0.09em;
    margin-bottom: 0.6rem;
}}
.kpi-value {{
    font-size: 2.4rem;
    font-weight: 800;
    color: {C['text_primary']};
    line-height: 1;
    letter-spacing: -0.03em;
}}
.kpi-sub {{
    font-size: 0.74rem;
    color: {C['text_muted']};
    margin-top: 0.35rem;
}}

/* ── Section header ── */
.sec-head {{
    font-size: 0.88rem;
    font-weight: 700;
    color: {C['text_primary']};
    margin-bottom: 0.2rem;
}}
.sec-sub {{
    font-size: 0.76rem;
    color: {C['text_muted']};
    margin-bottom: 1rem;
}}

/* ── Tags ── */
.tag {{
    display: inline-block; border-radius: 6px; padding: 2px 10px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
}}
.tag-positive {{ background:{C['positive_bg']}; color:{C['positive']}; }}
.tag-negative {{ background:{C['negative_bg']}; color:{C['negative']}; }}
.tag-mixed    {{ background:{C['mixed_bg']};    color:{C['mixed']};    }}
.tag-neutral  {{ background:{C['neutral_bg']};  color:{C['text_secondary']}; }}
.tag-hot      {{ background:{C['hot_bg']};      color:{C['hot']};      }}
.tag-warm     {{ background:{C['warm_bg']};     color:{C['warm']};     }}
.tag-cold     {{ background:{C['cold_bg']};     color:{C['cold']};     }}

/* ── Table ── */
.calls-table {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 14px;
    overflow: hidden;
    width: 100%;
}}
.calls-table table {{ width:100%; border-collapse:collapse; font-size:0.83rem; }}
.calls-table thead tr {{
    background: {C['bg']};
    border-bottom: 1px solid {C['border']};
}}
.calls-table th {{
    padding: 10px 16px;
    text-align: left;
    font-size: 0.68rem;
    font-weight: 700;
    color: {C['text_muted']};
    text-transform: uppercase;
    letter-spacing: 0.07em;
    white-space: nowrap;
}}
.calls-table tbody tr {{ border-bottom: 1px solid {C['border']}; }}
.calls-table tbody tr:last-child {{ border-bottom: none; }}
.calls-table tbody tr:hover {{ background: #f8fafc; }}
.calls-table td {{ padding: 10px 16px; vertical-align: middle; }}

/* ── Detail panels ── */
.dp {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
}}
.dp-label {{
    font-size: 0.68rem; font-weight: 700; color: {C['text_muted']};
    text-transform: uppercase; letter-spacing: 0.09em; margin-bottom: 0.4rem;
}}
.dp-value {{ font-size: 0.88rem; color: {C['text_primary']}; line-height: 1.6; }}

.transcript-box {{
    background: {C['bg']};
    border: 1px solid {C['border']};
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    font-size: 0.82rem;
    color: {C['text_secondary']};
    line-height: 1.9;
    max-height: 340px;
    overflow-y: auto;
    white-space: pre-wrap;
}}
.email-box {{
    background: {C['bg']};
    border: 1px solid {C['border']};
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    font-size: 0.87rem;
    color: {C['text_primary']};
    line-height: 1.85;
    white-space: pre-wrap;
}}
.quote-bar {{
    border-left: 3px solid {C['accent']};
    padding: 0.6rem 1rem;
    background: {C['accent_light']};
    border-radius: 0 8px 8px 0;
    font-style: italic;
    color: {C['text_secondary']};
    font-size: 0.86rem;
    margin: 0.8rem 0;
}}
.action-row {{
    display: flex; gap: 0.7rem; align-items: flex-start;
    padding: 0.65rem 0; border-bottom: 1px solid {C['border']};
    font-size: 0.86rem; color: {C['text_primary']};
}}
.action-row:last-child {{ border-bottom: none; }}
.action-num {{
    min-width: 22px; height: 22px; background: {C['accent_light']};
    color: {C['accent']}; font-weight: 700; font-size: 0.7rem;
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 1px;
}}

/* ── Buttons ── */
.stButton > button {{
    background: {C['accent']} !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.84rem !important;
    padding: 0.55rem 1.4rem !important;
    width: 100% !important;
    transition: background 0.15s !important;
    letter-spacing: 0.01em !important;
}}
.stButton > button:hover {{ background: {C['accent_dk']} !important; }}

/* ── Inputs ── */
div[data-testid="stTextInput"] input {{
    border-radius: 8px !important;
    border: 1px solid {C['border']} !important;
    font-size: 0.86rem !important;
    background: {C['surface']} !important;
}}
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stMultiSelect"] > div > div {{
    border-radius: 8px !important;
    border: 1px solid {C['border']} !important;
    background: {C['surface']} !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 2px;
    border-bottom: 1px solid {C['border']};
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: {C['text_muted']} !important;
    padding: 0.5rem 1.1rem !important;
    border-radius: 8px 8px 0 0 !important;
}}
.stTabs [aria-selected="true"] {{
    color: {C['accent']} !important;
    border-bottom: 2px solid {C['accent']} !important;
    background: {C['accent_light']} !important;
}}

/* ── Metric ── */
[data-testid="metric-container"] {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 12px;
    padding: 1rem 1.2rem;
}}

/* ── Entry cards ── */
.entry-card {{
    background: {C['surface']};
    border: 1.5px solid {C['border']};
    border-radius: 16px;
    padding: 2rem;
    height: 100%;
    transition: border-color 0.15s, box-shadow 0.15s;
}}
.entry-card:hover {{
    border-color: {C['accent']};
    box-shadow: 0 4px 24px rgba(14,165,233,0.10);
}}

/* ── File uploader ── */
[data-testid="stFileUploader"] section {{
    border: 2px dashed {C['border']} !important;
    border-radius: 10px !important;
    background: {C['surface']} !important;
}}

/* ── Spinner ── */
.stSpinner > div {{ border-top-color: {C['accent']} !important; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for key, val in [
    ("state", "empty"),
    ("results_df", None),
    ("total_available", 0),
    ("source_label", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = val

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def sent_tag(v):
    k = v.lower() if v else "neutral"
    if k not in ("positive","negative","mixed","neutral"): k = "neutral"
    return f'<span class="tag tag-{k}">{v}</span>'

def lead_tag(v):
    k = v.lower() if v else "cold"
    if k not in ("hot","warm","cold"): k = "cold"
    return f'<span class="tag tag-{k}">{v}</span>'

def score_html(n):
    n = int(n) if str(n).isdigit() else 0
    dots = "".join(
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:3px;background:{"#0ea5e9" if i<=n else C["border"]};"></span>'
        for i in range(1,6)
    )
    return dots

def chart_layout(**kwargs):
    """Base plotly layout — no showlegend so callers can set it freely."""
    base = dict(
        plot_bgcolor=C["surface"],
        paper_bgcolor=C["surface"],
        font=dict(family="Plus Jakarta Sans, sans-serif", color=C["text_secondary"], size=11),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor=C["border"], zerolinecolor=C["border"], title=None),
        yaxis=dict(gridcolor=C["border"], zerolinecolor=C["border"], title=None),
    )
    base.update(kwargs)
    return base

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — filters shown only in dashboard state
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar(df: pd.DataFrame):
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 1rem 0 0.5rem 0;">
            <div class="logo" style="font-size:2rem;">Close<span>Call</span></div>
            <div class="logo-sub">Sales Intelligence</div>
        </div>
        <hr style="border-color:#2d3f5a; margin: 1rem 0 1.5rem 0;">
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:0.68rem;font-weight:700;color:#a8b4c8;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:1rem;">Dashboard Filters</div>', unsafe_allow_html=True)

        companies = sorted(df["company"].dropna().unique().tolist())
        sentiments = sorted(df["sentiment"].dropna().unique().tolist())
        lead_types = sorted(df["lead_type"].dropna().unique().tolist())
        outcomes   = sorted(df["outcome"].dropna().unique().tolist())

        sel_companies  = st.multiselect("Company",   companies,  default=companies,  key="f_company")
        sel_sentiments = st.multiselect("Sentiment", sentiments, default=sentiments, key="f_sentiment")
        sel_leads      = st.multiselect("Lead Type", lead_types, default=lead_types, key="f_lead")
        sel_outcomes   = st.multiselect("Outcome",   outcomes,   default=outcomes,   key="f_outcome")

        st.markdown('<hr style="border-color:#2d3f5a; margin: 1.2rem 0;">', unsafe_allow_html=True)
        if st.button("Reset Filters", key="reset_filters"):
            for k in ["f_company","f_sentiment","f_lead","f_outcome"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

        st.markdown('<hr style="border-color:#2d3f5a; margin: 1.2rem 0;">', unsafe_allow_html=True)
        if st.button("← New Analysis", key="new_analysis"):
            st.session_state.state = "empty"
            st.session_state.results_df = None
            st.cache_data.clear()
            for k in ["f_company","f_sentiment","f_lead","f_outcome"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

        st.markdown(f"""
        <div style="margin-top:1.5rem; font-size:0.72rem; color:#4a6080; line-height:1.6;">
            <div>{st.session_state.source_label}</div>
            <div style="margin-top:0.3rem;">Groq · LLaMA 3.3 70B</div>
        </div>
        """, unsafe_allow_html=True)

    # Apply filters and return filtered df
    filtered = df.copy()
    if sel_companies:  filtered = filtered[filtered["company"].isin(sel_companies)]
    if sel_sentiments: filtered = filtered[filtered["sentiment"].isin(sel_sentiments)]
    if sel_leads:      filtered = filtered[filtered["lead_type"].isin(sel_leads)]
    if sel_outcomes:   filtered = filtered[filtered["outcome"].isin(sel_outcomes)]
    return filtered

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY STATE
# ─────────────────────────────────────────────────────────────────────────────
def render_entry():
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 1.5rem 0;">
            <div class="logo" style="font-size:2rem;">Close<span>Call</span></div>
            <div class="logo-sub">Sales Intelligence</div>
        </div>
        <hr style="border-color:#2d3f5a;">
        <div style="margin-top:1.2rem; font-size:0.78rem; color:#4a6080; line-height:1.8;">
            <div>📊 Sentiment analysis</div>
            <div>🔥 Lead scoring (Hot/Warm/Cold)</div>
            <div>💬 Objection detection</div>
            <div>⭐ Rep performance scoring</div>
            <div>✉️ AI follow-up email writer</div>
        </div>
        """, unsafe_allow_html=True)

    # Hero
    st.markdown(f"""
    <div style="padding: 2.5rem 0 2rem 0; border-bottom: 1px solid {C['border']}; margin-bottom: 2.5rem;">
        <div class="logo">Close<span>Call</span></div>
        <div style="font-size:1rem; color:{C['text_secondary']}; margin-top:0.7rem; max-width:480px; line-height:1.6;">
            Turn sales call transcripts into actionable intelligence — sentiment, objections, lead scores, and follow-up emails in seconds.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_a, gap, col_b = st.columns([10, 1, 10])

    with col_a:
        st.markdown(f"""
        <div class="entry-card">
            <div style="font-size:1.5rem; margin-bottom:0.8rem;">📂</div>
            <div style="font-size:0.95rem; font-weight:700; color:{C['text_primary']}; margin-bottom:0.4rem;">Upload Your Transcripts</div>
            <div style="font-size:0.82rem; color:{C['text_secondary']}; line-height:1.6; margin-bottom:1.2rem;">
                Upload a CSV with a <code>transcript</code> or <code>content</code> column.<br>
                Optional: <code>id</code>, <code>company</code> columns.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        uploaded = st.file_uploader("", type=["csv"], label_visibility="collapsed")
        if uploaded:
            if st.button("Analyze Uploaded File", key="btn_upload"):
                try:
                    transcripts = load_csv_transcripts(uploaded)
                    st.session_state.total_available = len(transcripts)
                    st.session_state.source_label = f"{len(transcripts)} uploaded calls"
                    st.session_state["_transcripts_to_process"] = transcripts
                    st.session_state.state = "processing"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")

    with gap:
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:center;height:200px;">
            <span style="font-size:0.75rem;font-weight:700;color:{C['text_muted']};letter-spacing:0.1em;text-transform:uppercase;">or</span>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown(f"""
        <div class="entry-card">
            <div style="font-size:1.5rem; margin-bottom:0.8rem;">🗂️</div>
            <div style="font-size:0.95rem; font-weight:700; color:{C['text_primary']}; margin-bottom:0.4rem;">Use Sample Dataset</div>
            <div style="font-size:0.82rem; color:{C['text_secondary']}; line-height:1.6; margin-bottom:1.2rem;">
                103 real sales call transcripts across fashion, real estate, finance, healthcare & tech.
                No upload needed.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("Analyze Sample Data  ·  103 Calls", key="btn_sample"):
            with st.spinner("Fetching transcripts from HuggingFace..."):
                transcripts = load_sample_transcripts()
            st.session_state.total_available = len(transcripts)
            st.session_state.source_label = f"Sample dataset · {len(transcripts)} calls"
            st.session_state["_transcripts_to_process"] = transcripts
            st.session_state.state = "processing"
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# PROCESSING STATE
# ─────────────────────────────────────────────────────────────────────────────
def render_processing():
    transcripts = st.session_state.get("_transcripts_to_process", [])
    if not transcripts:
        st.session_state.state = "empty"
        st.rerun()
        return

    st.markdown(f"""
    <div style="padding:3rem 0 1rem 0; text-align:center;">
        <div style="font-size:1.3rem; font-weight:700; color:{C['text_primary']}; margin-bottom:0.4rem;">Analyzing calls…</div>
        <div style="font-size:0.85rem; color:{C['text_muted']};">Groq LLaMA 3.3 is reading each transcript and extracting insights.</div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 4, 1])
    with col:
        progress = st.progress(0, text="Starting…")

    results = analyze_batch(transcripts, progress)
    progress.empty()
    st.session_state.results_df = pd.DataFrame(results)
    st.session_state.state = "dashboard"
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────────────────────────────────────
def render_kpis(df: pd.DataFrame):
    total = len(df)
    total_avail = st.session_state.total_available
    pos_pct  = round(len(df[df["sentiment"]=="Positive"]) / total * 100) if total else 0
    neg_pct  = round(len(df[df["sentiment"]=="Negative"]) / total * 100) if total else 0
    hot      = len(df[df["lead_type"]=="Hot"])

    sampling = f"Showing {total} of {total_avail}" if total < total_avail else f"{total} calls processed"

    k1, k2, k3, k4 = st.columns(4)
    for col, label, value, sub in [
        (k1, "Calls Analyzed",     str(total),   sampling),
        (k2, "Positive Sentiment", f"{pos_pct}%", f"{len(df[df['sentiment']=='Positive'])} calls"),
        (k3, "Negative Sentiment", f"{neg_pct}%", f"{len(df[df['sentiment']=='Negative'])} calls"),
        (k4, "Hot Leads",          str(hot),      "Sale likely"),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────────────────────
def render_charts(df: pd.DataFrame):
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="sec-head">Sentiment Distribution</div>', unsafe_allow_html=True)
        sent = df["sentiment"].value_counts().reset_index()
        sent.columns = ["Sentiment", "Calls"]
        cmap = {"Positive": C["positive"], "Negative": C["negative"],
                "Mixed": C["mixed"], "Neutral": C["text_muted"]}
        fig = px.bar(sent, x="Sentiment", y="Calls", color="Sentiment",
                     color_discrete_map=cmap, text="Calls")
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(showlegend=False, **chart_layout())
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown('<div class="sec-head">Top Objections</div>', unsafe_allow_html=True)
        obj = df[
            df["top_objection"].notna() &
            ~df["top_objection"].str.lower().isin(["none","unknown","—"])
        ]["top_objection"].apply(lambda x: x[:48]+"…" if len(x)>48 else x)
        if len(obj):
            oc = obj.value_counts().head(7).reset_index()
            oc.columns = ["Objection", "Count"]
            fig2 = px.bar(oc, x="Count", y="Objection", orientation="h",
                          color="Count",
                          color_continuous_scale=[C["accent_light"], C["accent"]],
                          text="Count")
            fig2.update_traces(textposition="outside", marker_line_width=0)
            fig2.update_layout(showlegend=False, coloraxis_showscale=False,
                               yaxis=dict(autorange="reversed", gridcolor=C["border"], title=None),
                               xaxis=dict(gridcolor=C["border"], title=None),
                               **{k:v for k,v in chart_layout().items() if k not in ("xaxis","yaxis")})
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No objections detected in current selection.")

# ─────────────────────────────────────────────────────────────────────────────
# CALLS TABLE
# ─────────────────────────────────────────────────────────────────────────────
def render_calls_table(df: pd.DataFrame):
    st.markdown("---")
    st.markdown('<div class="sec-head">All Calls</div>', unsafe_allow_html=True)

    s1, s2 = st.columns([4, 2])
    with s1:
        search = st.text_input("", placeholder="🔍  Search by company, issue, objection…", label_visibility="collapsed", key="tbl_search")

    filtered = df.copy()
    if search:
        mask = (
            filtered["id"].astype(str).str.contains(search, case=False, na=False) |
            filtered["company"].astype(str).str.contains(search, case=False, na=False) |
            filtered["key_issue"].astype(str).str.contains(search, case=False, na=False) |
            filtered["top_objection"].astype(str).str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    st.markdown(f'<div style="font-size:0.76rem;color:{C["text_muted"]};margin-bottom:0.7rem;">{len(filtered)} of {len(df)} calls</div>', unsafe_allow_html=True)

    if filtered.empty:
        st.info("No calls match your search.")
        return

    rows_html = ""
    for _, row in filtered.head(60).iterrows():
        obj   = str(row.get("top_objection","—"))
        nstep = str(row.get("next_step","—"))
        rows_html += f"""
        <tr>
            <td style="font-weight:600;color:{C['text_primary']};">{row['id']}</td>
            <td style="color:{C['text_secondary']};">{row['company']}</td>
            <td>{sent_tag(row.get('sentiment','—'))}</td>
            <td>{lead_tag(row.get('lead_type','—'))}</td>
            <td style="color:{C['text_secondary']};max-width:200px;">{obj[:58]}{"…" if len(obj)>58 else ""}</td>
            <td style="color:{C['text_secondary']};max-width:180px;">{nstep[:52]}{"…" if len(nstep)>52 else ""}</td>
        </tr>"""

    st.markdown(f"""
    <div class="calls-table">
        <table>
            <thead><tr>
                <th>Call ID</th><th>Company</th><th>Sentiment</th>
                <th>Lead</th><th>Key Objection</th><th>Next Step</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

    if len(filtered) > 60:
        st.caption(f"Showing first 60 of {len(filtered)} results.")

    st.markdown("<br>", unsafe_allow_html=True)
    render_detail(filtered)

# ─────────────────────────────────────────────────────────────────────────────
# DETAIL VIEW
# ─────────────────────────────────────────────────────────────────────────────
def render_detail(df: pd.DataFrame):
    st.markdown('<div class="sec-head">Call Detail</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-sub">Select any call to view transcript, insights, actions and follow-up email.</div>', unsafe_allow_html=True)

    selected = st.selectbox("", df["id"].tolist(), label_visibility="collapsed", key="detail_sel")
    row = df[df["id"] == selected].iloc[0]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sentiment",  row.get("sentiment","—"))
    m2.metric("Lead Type",  row.get("lead_type","—"))
    m3.metric("Resolution", row.get("resolution_status","—"))
    m4.metric("Rep Score",  f"{row.get('rep_score','—')}/5")

    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["Transcript", "AI Insights", "Recommended Actions", "Follow-up Email"])

    with t1:
        content = str(row.get("content","No transcript."))
        display = content.replace("**Sales Rep**","🎙 Sales Rep").replace("**Customer**","👤 Customer")
        st.markdown(f'<div class="transcript-box">{display}</div>', unsafe_allow_html=True)

    with t2:
        i1, i2 = st.columns(2)
        with i1:
            for label, field in [("Summary","summary"),("Sentiment Arc","sentiment_arc"),("Key Issue","key_issue")]:
                st.markdown(f'<div class="dp"><div class="dp-label">{label}</div><div class="dp-value">{row.get(field,"—")}</div></div>', unsafe_allow_html=True)
        with i2:
            for label, field in [("Top Objection","top_objection"),("Sales Outcome","outcome")]:
                st.markdown(f'<div class="dp"><div class="dp-label">{label}</div><div class="dp-value">{row.get(field,"—")}</div></div>', unsafe_allow_html=True)
            rep_score = int(row.get("rep_score", 0)) if str(row.get("rep_score","0")).isdigit() else 0
            st.markdown(f"""
            <div class="dp">
                <div class="dp-label">Rep Performance</div>
                <div style="margin-bottom:0.4rem;">{score_html(rep_score)}</div>
                <div class="dp-value">{row.get("rep_score_reason","—")}</div>
            </div>
            """, unsafe_allow_html=True)
        q = row.get("standout_quote","")
        if q and q != "—":
            st.markdown(f'<div class="quote-bar">"{q}"</div>', unsafe_allow_html=True)

    with t3:
        ns = row.get("next_step","")
        if ns:
            st.markdown(f"""
            <div class="dp" style="border-left:3px solid {C['accent']};">
                <div class="dp-label">Immediate Next Step</div>
                <div class="dp-value" style="font-weight:700;color:{C['accent']};">{ns}</div>
            </div>
            """, unsafe_allow_html=True)
        actions = row.get("recommended_actions", [])
        if isinstance(actions, str):
            import json as _j
            try: actions = _j.loads(actions)
            except: actions = [actions]
        if actions:
            items = "".join(f'<div class="action-row"><div class="action-num">{i}</div><div>{a}</div></div>' for i,a in enumerate(actions,1))
            st.markdown(f'<div class="dp"><div class="dp-label">Action Items</div>{items}</div>', unsafe_allow_html=True)

    with t4:
        email_key = f"email_{selected}"
        if email_key not in st.session_state:
            st.session_state[email_key] = None

        if st.session_state[email_key] is None:
            st.markdown(f'<div style="font-size:0.84rem;color:{C["text_muted"]};margin-bottom:1rem;">Generate a personalized follow-up email based on this call.</div>', unsafe_allow_html=True)
            _, bc, _ = st.columns([2,3,2])
            with bc:
                if st.button("Generate Follow-up Email", key=f"gen_{selected}"):
                    with st.spinner("Writing email…"):
                        email = generate_email(
                            summary=str(row.get("summary","")),
                            key_issue=str(row.get("key_issue","")),
                            next_step=str(row.get("next_step","")),
                            sentiment=str(row.get("sentiment","")),
                            transcript_excerpt=str(row.get("content",""))[:800],
                        )
                    st.session_state[email_key] = email
                    st.rerun()
        else:
            st.markdown(f'<div class="email-box">{st.session_state[email_key]}</div>', unsafe_allow_html=True)
            _, rc, _ = st.columns([3,2,3])
            with rc:
                if st.button("Regenerate", key=f"regen_{selected}"):
                    st.session_state[email_key] = None
                    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def render_dashboard():
    df_all = st.session_state.results_df
    df = render_sidebar(df_all)   # sidebar renders filters and returns filtered df

    st.markdown(f"""
    <div style="padding:1.5rem 0 2rem 0; border-bottom:1px solid {C['border']}; margin-bottom:2rem;">
        <div class="logo">Close<span>Call</span></div>
        <div style="font-size:0.78rem;color:{C['text_muted']};margin-top:0.3rem;">{st.session_state.source_label}</div>
    </div>
    """, unsafe_allow_html=True)

    render_kpis(df)
    st.markdown("<br>", unsafe_allow_html=True)
    render_charts(df)
    render_calls_table(df)

# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
state = st.session_state.state

if state == "empty":
    render_entry()
elif state == "processing":
    render_processing()
elif state == "dashboard":
    if st.session_state.results_df is not None:
        render_dashboard()
    else:
        st.session_state.state = "empty"
        st.rerun()
