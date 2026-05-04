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
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS & CSS
# ─────────────────────────────────────────────────────────────────────────────
COLORS = {
    "bg": "#f5f6f8",
    "surface": "#ffffff",
    "border": "#e4e7ec",
    "border_strong": "#d0d5dd",
    "text_primary": "#101828",
    "text_secondary": "#475467",
    "text_muted": "#98a2b3",
    "accent": "#4f46e5",
    "accent_light": "#eef2ff",
    "accent_mid": "#c7d2fe",
    "positive": "#027a48",
    "positive_bg": "#ecfdf3",
    "negative": "#b42318",
    "negative_bg": "#fef3f2",
    "mixed": "#b54708",
    "mixed_bg": "#fffaeb",
    "neutral": "#344054",
    "neutral_bg": "#f2f4f7",
    "hot": "#c4320a",
    "hot_bg": "#fff4ed",
    "warm": "#b54708",
    "warm_bg": "#fffaeb",
    "cold": "#175cd3",
    "cold_bg": "#eff8ff",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=Mulish:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Mulish', sans-serif;
    color: {COLORS['text_primary']};
}}
.stApp {{
    background: {COLORS['bg']};
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{ background: {COLORS['surface']} !important; border-right: 1px solid {COLORS['border']}; }}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header {{ visibility: hidden; }}
[data-testid="stToolbar"] {{ display: none; }}

/* ── Top nav bar ── */
.topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0 1.5rem 0;
    border-bottom: 1px solid {COLORS['border']};
    margin-bottom: 2.5rem;
}}
.topbar-logo {{
    font-family: 'Sora', sans-serif;
    font-weight: 700;
    font-size: 1.35rem;
    color: {COLORS['text_primary']};
    letter-spacing: -0.02em;
}}
.topbar-logo span {{
    color: {COLORS['accent']};
}}
.topbar-badge {{
    background: {COLORS['accent_light']};
    color: {COLORS['accent']};
    font-family: 'Mulish', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid {COLORS['accent_mid']};
    letter-spacing: 0.02em;
}}

/* ── Entry cards ── */
.entry-card {{
    background: {COLORS['surface']};
    border: 1.5px solid {COLORS['border']};
    border-radius: 14px;
    padding: 2rem 2rem 1.8rem 2rem;
    transition: border-color 0.15s, box-shadow 0.15s;
    height: 100%;
}}
.entry-card:hover {{
    border-color: {COLORS['accent_mid']};
    box-shadow: 0 4px 20px rgba(79,70,229,0.07);
}}
.entry-card-icon {{
    font-size: 1.8rem;
    margin-bottom: 0.8rem;
}}
.entry-card-title {{
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    color: {COLORS['text_primary']};
    margin-bottom: 0.4rem;
}}
.entry-card-desc {{
    font-size: 0.83rem;
    color: {COLORS['text_secondary']};
    line-height: 1.6;
    margin-bottom: 1.2rem;
}}
.entry-divider {{
    text-align: center;
    font-size: 0.78rem;
    color: {COLORS['text_muted']};
    font-family: 'Mulish', sans-serif;
    font-weight: 500;
    margin: 1rem 0;
    position: relative;
}}
.entry-divider::before {{
    content: '';
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 1px;
    background: {COLORS['border']};
    z-index: 0;
}}
.entry-divider span {{
    background: {COLORS['bg']};
    padding: 0 12px;
    position: relative;
    z-index: 1;
}}

/* ── KPI Cards ── */
.kpi-card {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
}}
.kpi-label {{
    font-size: 0.78rem;
    font-weight: 600;
    color: {COLORS['text_secondary']};
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.6rem;
}}
.kpi-value {{
    font-family: 'Sora', sans-serif;
    font-weight: 700;
    font-size: 2.2rem;
    color: {COLORS['text_primary']};
    line-height: 1;
    letter-spacing: -0.02em;
}}
.kpi-sub {{
    font-size: 0.76rem;
    color: {COLORS['text_muted']};
    margin-top: 0.4rem;
}}

/* ── Section headers ── */
.section-header {{
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
    color: {COLORS['text_primary']};
    margin-bottom: 0.3rem;
}}
.section-desc {{
    font-size: 0.8rem;
    color: {COLORS['text_muted']};
    margin-bottom: 1.2rem;
}}

/* ── Chart containers ── */
.chart-card {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 1.4rem 1.6rem 0.8rem 1.6rem;
}}

/* ── Lead type tags ── */
.tag {{
    display: inline-block;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}}
.tag-hot {{ background: {COLORS['hot_bg']}; color: {COLORS['hot']}; }}
.tag-warm {{ background: {COLORS['warm_bg']}; color: {COLORS['warm']}; }}
.tag-cold {{ background: {COLORS['cold_bg']}; color: {COLORS['cold']}; }}
.tag-positive {{ background: {COLORS['positive_bg']}; color: {COLORS['positive']}; }}
.tag-negative {{ background: {COLORS['negative_bg']}; color: {COLORS['negative']}; }}
.tag-mixed {{ background: {COLORS['mixed_bg']}; color: {COLORS['mixed']}; }}
.tag-neutral {{ background: {COLORS['neutral_bg']}; color: {COLORS['neutral']}; }}

/* ── Detail panels ── */
.detail-panel {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}}
.detail-label {{
    font-size: 0.72rem;
    font-weight: 700;
    color: {COLORS['text_muted']};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
}}
.detail-value {{
    font-size: 0.9rem;
    color: {COLORS['text_primary']};
    line-height: 1.6;
}}
.transcript-box {{
    background: {COLORS['bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    font-size: 0.83rem;
    color: {COLORS['text_secondary']};
    line-height: 1.85;
    max-height: 320px;
    overflow-y: auto;
    white-space: pre-wrap;
}}
.action-item {{
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.6rem 0;
    border-bottom: 1px solid {COLORS['border']};
    font-size: 0.86rem;
    color: {COLORS['text_primary']};
}}
.action-item:last-child {{ border-bottom: none; }}
.action-num {{
    background: {COLORS['accent_light']};
    color: {COLORS['accent']};
    font-weight: 700;
    font-size: 0.7rem;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 1px;
}}
.email-box {{
    background: {COLORS['bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    font-size: 0.87rem;
    color: {COLORS['text_primary']};
    line-height: 1.8;
    white-space: pre-wrap;
}}
.standout-quote {{
    border-left: 3px solid {COLORS['accent']};
    padding: 0.6rem 1rem;
    margin: 0.8rem 0;
    font-style: italic;
    color: {COLORS['text_secondary']};
    font-size: 0.88rem;
    background: {COLORS['accent_light']};
    border-radius: 0 6px 6px 0;
}}
.score-row {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
}}
.score-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
}}

/* ── Empty state ── */
.empty-state {{
    text-align: center;
    padding: 4rem 2rem;
}}
.empty-icon {{ font-size: 2.5rem; margin-bottom: 1rem; }}
.empty-title {{
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    font-size: 1.2rem;
    color: {COLORS['text_primary']};
    margin-bottom: 0.5rem;
}}
.empty-desc {{
    font-size: 0.85rem;
    color: {COLORS['text_muted']};
    max-width: 400px;
    margin: 0 auto;
    line-height: 1.6;
}}

/* ── Progress bar color ── */
.stProgress > div > div {{ background-color: {COLORS['accent']} !important; }}

/* ── Buttons ── */
.stButton > button {{
    background: {COLORS['accent']} !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Mulish', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.55rem 1.4rem !important;
    width: 100%;
    transition: opacity 0.15s !important;
}}
.stButton > button:hover {{ opacity: 0.88 !important; }}

/* ── Selectbox / inputs ── */
div[data-testid="stSelectbox"] label,
div[data-testid="stMultiSelect"] label,
div[data-testid="stTextInput"] label {{
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: {COLORS['text_secondary']} !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}}
div[data-testid="stTextInput"] input {{
    border-radius: 8px !important;
    border-color: {COLORS['border']} !important;
    font-size: 0.88rem !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 1px solid {COLORS['border']};
}}
.stTabs [data-baseweb="tab"] {{
    font-family: 'Mulish', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: {COLORS['text_muted']} !important;
    padding: 0.5rem 1rem !important;
    border-radius: 6px 6px 0 0 !important;
}}
.stTabs [aria-selected="true"] {{
    color: {COLORS['accent']} !important;
    border-bottom: 2px solid {COLORS['accent']} !important;
    background: {COLORS['accent_light']} !important;
}}

/* ── Horizontal rule ── */
hr {{ border-color: {COLORS['border']} !important; }}

/* ── File uploader ── */
[data-testid="stFileUploader"] {{
    border: 1.5px dashed {COLORS['border_strong']} !important;
    border-radius: 10px !important;
    padding: 0.5rem !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {COLORS['accent_mid']} !important;
}}

/* ── Metric overrides ── */
[data-testid="metric-container"] {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 1rem 1.2rem;
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
for key, default in [
    ("state", "empty"),        # empty | processing | dashboard
    ("results_df", None),
    ("total_available", 0),
    ("source_label", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def sentiment_tag(val: str) -> str:
    cls = f"tag-{val.lower()}" if val.lower() in ["positive","negative","mixed","neutral"] else "tag-neutral"
    return f'<span class="tag {cls}">{val}</span>'

def lead_tag(val: str) -> str:
    cls = f"tag-{val.lower()}" if val.lower() in ["hot","warm","cold"] else "tag-neutral"
    return f'<span class="tag {cls}">{val}</span>'

def score_dots(score: int) -> str:
    dots = ""
    for i in range(1, 6):
        color = COLORS["accent"] if i <= score else COLORS["border"]
        dots += f'<span class="score-dot" style="background:{color};display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:3px;"></span>'
    return f'<div class="score-row">{dots}</div>'

def plot_config():
    return dict(
        plot_bgcolor=COLORS["surface"],
        paper_bgcolor=COLORS["surface"],
        font=dict(family="Mulish, sans-serif", color=COLORS["text_secondary"], size=12),
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# TOP NAV
# ─────────────────────────────────────────────────────────────────────────────
def render_topbar():
    st.markdown("""
    <div class="topbar">
        <div class="topbar-logo">Close<span>Call</span></div>
        <div class="topbar-badge">AI Sales Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE / ENTRY
# ─────────────────────────────────────────────────────────────────────────────
def render_entry():
    st.markdown("""
    <div style="text-align:center; margin-bottom: 2.5rem;">
        <div style="font-family:'Sora',sans-serif; font-weight:700; font-size:1.7rem; color:#101828; letter-spacing:-0.02em; margin-bottom:0.5rem;">
            Turn call transcripts into sales insights
        </div>
        <div style="font-size:0.9rem; color:#667085; max-width:520px; margin:0 auto; line-height:1.6;">
            CloseCall uses AI to analyze sentiment, identify objections, score rep performance, 
            and surface hot leads — in seconds.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_div, col_b = st.columns([10, 1, 10])

    # ── Option A: Upload CSV
    with col_a:
        st.markdown("""
        <div class="entry-card">
            <div class="entry-card-icon">📂</div>
            <div class="entry-card-title">Upload Your Transcripts</div>
            <div class="entry-card-desc">
                Upload a CSV file with a <code>transcript</code> or <code>content</code> column.
                Optional columns: <code>id</code>, <code>company</code>.
            </div>
        </div>
        """, unsafe_allow_html=True)
        uploaded = st.file_uploader("", type=["csv"], label_visibility="collapsed")
        if uploaded:
            if st.button("Analyze Uploaded Transcripts", key="btn_upload"):
                try:
                    transcripts = load_csv_transcripts(uploaded)
                    st.session_state.total_available = len(transcripts)
                    st.session_state.source_label = f"{len(transcripts)} uploaded calls"
                    _run_analysis(transcripts)
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")

    # ── Divider
    with col_div:
        st.markdown("""
        <div style="display:flex; align-items:center; justify-content:center; height:100%; padding-top:3rem;">
            <div style="writing-mode:vertical-rl; color:#98a2b3; font-size:0.8rem; font-weight:600; 
                        letter-spacing:0.08em; text-transform:uppercase;">or</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Option B: Sample data
    with col_b:
        st.markdown("""
        <div class="entry-card">
            <div class="entry-card-icon">🗂️</div>
            <div class="entry-card-title">Use Sample Dataset</div>
            <div class="entry-card-desc">
                103 real sales call transcripts across 10+ companies — fashion, real estate, 
                finance, healthcare, and tech. No upload needed.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
        if st.button("Analyze Sample Data  ·  103 Sales Calls", key="btn_sample"):
            with st.spinner("Fetching transcripts from HuggingFace..."):
                transcripts = load_sample_transcripts()
            st.session_state.total_available = len(transcripts)
            st.session_state.source_label = f"Sample dataset · {len(transcripts)} calls"
            _run_analysis(transcripts)

    # ── Feature pills
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex; gap:0.6rem; justify-content:center; flex-wrap:wrap; margin-top:1.5rem;">
        <span style="background:#f2f4f7;color:#344054;border-radius:20px;padding:4px 14px;font-size:0.76rem;font-weight:600;">📊 Sentiment Analysis</span>
        <span style="background:#f2f4f7;color:#344054;border-radius:20px;padding:4px 14px;font-size:0.76rem;font-weight:600;">🔥 Lead Scoring</span>
        <span style="background:#f2f4f7;color:#344054;border-radius:20px;padding:4px 14px;font-size:0.76rem;font-weight:600;">💬 Objection Detection</span>
        <span style="background:#f2f4f7;color:#344054;border-radius:20px;padding:4px 14px;font-size:0.76rem;font-weight:600;">⭐ Rep Performance</span>
        <span style="background:#f2f4f7;color:#344054;border-radius:20px;padding:4px 14px;font-size:0.76rem;font-weight:600;">✉️ Follow-up Email Generator</span>
    </div>
    """, unsafe_allow_html=True)


def _run_analysis(transcripts: list):
    st.session_state.state = "processing"
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PROCESSING STATE
# ─────────────────────────────────────────────────────────────────────────────
def render_processing(transcripts: list):
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem 0;">
        <div style="font-family:'Sora',sans-serif; font-weight:600; font-size:1.2rem; color:#101828; margin-bottom:0.4rem;">
            Analyzing calls...
        </div>
        <div style="font-size:0.85rem; color:#667085;">
            Groq LLaMA 3.3 is reading each transcript and extracting insights.
        </div>
    </div>
    """, unsafe_allow_html=True)
    progress = st.progress(0, text="Starting...")
    results = analyze_batch(transcripts, progress)
    progress.empty()
    st.session_state.results_df = pd.DataFrame(results)
    st.session_state.state = "dashboard"
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD — KPI ROW
# ─────────────────────────────────────────────────────────────────────────────
def render_kpis(df: pd.DataFrame, total_available: int):
    total = len(df)
    positive_pct = round(len(df[df["sentiment"] == "Positive"]) / total * 100) if total else 0
    negative_pct = round(len(df[df["sentiment"] == "Negative"]) / total * 100) if total else 0
    hot_leads = len(df[df["lead_type"] == "Hot"])

    sampling_note = ""
    if total < total_available:
        sampling_note = f'<div class="kpi-sub">Showing {total} of {total_available}</div>'
    else:
        sampling_note = f'<div class="kpi-sub">All calls processed</div>'

    k1, k2, k3, k4 = st.columns(4)
    cards = [
        (k1, "Calls Analyzed", str(total), sampling_note),
        (k2, "Positive Sentiment", f"{positive_pct}%", f'<div class="kpi-sub">{len(df[df["sentiment"] == "Positive"])} calls</div>'),
        (k3, "Negative Sentiment", f"{negative_pct}%", f'<div class="kpi-sub">{len(df[df["sentiment"] == "Negative"])} calls</div>'),
        (k4, "Hot Leads", str(hot_leads), f'<div class="kpi-sub">Sale likely</div>'),
    ]
    for col, label, value, sub in cards:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                {sub}
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD — CHARTS
# ─────────────────────────────────────────────────────────────────────────────
def render_charts(df: pd.DataFrame):
    c1, c2 = st.columns(2)

    # Sentiment distribution
    with c1:
        st.markdown('<div class="section-header">Sentiment Distribution</div>', unsafe_allow_html=True)
        sent = df["sentiment"].value_counts().reset_index()
        sent.columns = ["Sentiment", "Calls"]
        color_map = {
            "Positive": COLORS["positive"],
            "Negative": COLORS["negative"],
            "Mixed": "#f79009",
            "Neutral": COLORS["text_muted"],
            "Unknown": COLORS["border"],
        }
        fig = px.bar(
            sent, x="Sentiment", y="Calls",
            color="Sentiment", color_discrete_map=color_map,
            text="Calls",
        )
        fig.update_traces(textposition="outside", textfont_size=13, marker_line_width=0)
        fig.update_layout(
            **plot_config(),
            showlegend=False,
            xaxis=dict(title=None, gridcolor=COLORS["border"]),
            yaxis=dict(title=None, gridcolor=COLORS["border"]),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Top objections
    with c2:
        st.markdown('<div class="section-header">Top Objections</div>', unsafe_allow_html=True)
        obj_series = df[
            df["top_objection"].notna() &
            (df["top_objection"].str.lower() != "none") &
            (df["top_objection"].str.lower() != "unknown")
        ]["top_objection"]
        if len(obj_series):
            # Truncate long objections for display
            obj_counts = obj_series.apply(lambda x: x[:45] + "…" if len(x) > 45 else x).value_counts().head(8).reset_index()
            obj_counts.columns = ["Objection", "Count"]
            fig2 = px.bar(
                obj_counts, x="Count", y="Objection", orientation="h",
                color="Count",
                color_continuous_scale=[COLORS["accent_light"], COLORS["accent"]],
                text="Count",
            )
            fig2.update_traces(textposition="outside", textfont_size=11, marker_line_width=0)
            fig2.update_layout(
                **plot_config(),
                coloraxis_showscale=False,
                xaxis=dict(title=None, gridcolor=COLORS["border"]),
                yaxis=dict(title=None, gridcolor=COLORS["border"], autorange="reversed"),
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<div class="empty-state"><div class="empty-desc">No objections detected in current filter.</div></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD — CALLS TABLE + DETAIL
# ─────────────────────────────────────────────────────────────────────────────
def render_calls_table(df: pd.DataFrame):
    st.markdown("---")
    st.markdown('<div class="section-header" style="margin-bottom:1rem;">All Calls</div>', unsafe_allow_html=True)

    # ── Filters row
    f1, f2, f3, f4 = st.columns([3, 2, 2, 2])
    with f1:
        search = st.text_input("Search", placeholder="Search by company, issue, objection…", label_visibility="collapsed")
    with f2:
        sentiment_opts = ["All"] + sorted(df["sentiment"].dropna().unique().tolist())
        sentiment_f = st.selectbox("Sentiment", sentiment_opts, label_visibility="visible")
    with f3:
        lead_opts = ["All"] + sorted(df["lead_type"].dropna().unique().tolist())
        lead_f = st.selectbox("Lead Type", lead_opts, label_visibility="visible")
    with f4:
        company_opts = ["All"] + sorted(df["company"].dropna().unique().tolist())
        company_f = st.selectbox("Company", company_opts, label_visibility="visible")

    # Apply filters
    filtered = df.copy()
    if search:
        mask = (
            filtered["id"].astype(str).str.contains(search, case=False, na=False) |
            filtered["key_issue"].astype(str).str.contains(search, case=False, na=False) |
            filtered["top_objection"].astype(str).str.contains(search, case=False, na=False) |
            filtered["company"].astype(str).str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]
    if sentiment_f != "All":
        filtered = filtered[filtered["sentiment"] == sentiment_f]
    if lead_f != "All":
        filtered = filtered[filtered["lead_type"] == lead_f]
    if company_f != "All":
        filtered = filtered[filtered["company"] == company_f]

    count_label = f"{len(filtered)} of {len(df)} calls" if len(filtered) != len(df) else f"{len(filtered)} calls"
    st.markdown(f'<div style="font-size:0.78rem; color:{COLORS["text_muted"]}; margin-bottom:0.8rem;">{count_label}</div>', unsafe_allow_html=True)

    if len(filtered) == 0:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <div class="empty-title">No calls match your filters</div>
            <div class="empty-desc">Try adjusting the search or filter criteria.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Render table
    st.markdown(f"""
    <div style="background:{COLORS['surface']}; border:1px solid {COLORS['border']}; border-radius:12px; overflow:hidden;">
    <table style="width:100%; border-collapse:collapse; font-size:0.84rem;">
    <thead>
    <tr style="background:{COLORS['bg']}; border-bottom:1px solid {COLORS['border']};">
        <th style="padding:10px 14px; text-align:left; font-weight:600; font-size:0.72rem; color:{COLORS['text_muted']}; text-transform:uppercase; letter-spacing:0.05em;">Call ID</th>
        <th style="padding:10px 14px; text-align:left; font-weight:600; font-size:0.72rem; color:{COLORS['text_muted']}; text-transform:uppercase; letter-spacing:0.05em;">Company</th>
        <th style="padding:10px 14px; text-align:left; font-weight:600; font-size:0.72rem; color:{COLORS['text_muted']}; text-transform:uppercase; letter-spacing:0.05em;">Sentiment</th>
        <th style="padding:10px 14px; text-align:left; font-weight:600; font-size:0.72rem; color:{COLORS['text_muted']}; text-transform:uppercase; letter-spacing:0.05em;">Lead</th>
        <th style="padding:10px 14px; text-align:left; font-weight:600; font-size:0.72rem; color:{COLORS['text_muted']}; text-transform:uppercase; letter-spacing:0.05em;">Key Objection</th>
        <th style="padding:10px 14px; text-align:left; font-weight:600; font-size:0.72rem; color:{COLORS['text_muted']}; text-transform:uppercase; letter-spacing:0.05em;">Next Step</th>
    </tr>
    </thead>
    <tbody>
    {"".join([
        f'''<tr style="border-bottom:1px solid {COLORS['border']};">
            <td style="padding:10px 14px; font-weight:500; color:{COLORS['text_primary']};">{row['id']}</td>
            <td style="padding:10px 14px; color:{COLORS['text_secondary']};">{row['company']}</td>
            <td style="padding:10px 14px;">{sentiment_tag(row.get('sentiment','—'))}</td>
            <td style="padding:10px 14px;">{lead_tag(row.get('lead_type','—'))}</td>
            <td style="padding:10px 14px; color:{COLORS['text_secondary']}; max-width:220px;">{str(row.get('top_objection','—'))[:60]}{"…" if len(str(row.get('top_objection',''))) > 60 else ""}</td>
            <td style="padding:10px 14px; color:{COLORS['text_secondary']}; max-width:200px;">{str(row.get('next_step','—'))[:55]}{"…" if len(str(row.get('next_step',''))) > 55 else ""}</td>
        </tr>'''
        for _, row in filtered.head(50).iterrows()
    ])}
    </tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)

    if len(filtered) > 50:
        st.markdown(f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]};margin-top:0.5rem;">Showing first 50 of {len(filtered)} filtered results.</div>', unsafe_allow_html=True)

    # ── Detail view
    st.markdown("<br>", unsafe_allow_html=True)
    render_detail_view(filtered)


# ─────────────────────────────────────────────────────────────────────────────
# DETAIL VIEW
# ─────────────────────────────────────────────────────────────────────────────
def render_detail_view(df: pd.DataFrame):
    st.markdown('<div class="section-header">Call Detail</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-desc">Select a call to view full transcript, AI insights, and recommended actions.</div>', unsafe_allow_html=True)

    call_ids = df["id"].tolist()
    selected_id = st.selectbox("Select call", call_ids, label_visibility="collapsed")
    row = df[df["id"] == selected_id].iloc[0]

    # Meta row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sentiment", row.get("sentiment", "—"))
    m2.metric("Lead Type", row.get("lead_type", "—"))
    m3.metric("Resolution", row.get("resolution_status", "—"))
    m4.metric("Rep Score", f"{row.get('rep_score', '—')}/5")

    st.markdown("<br>", unsafe_allow_html=True)

    tab_t, tab_i, tab_a, tab_e = st.tabs(["Transcript", "AI Insights", "Recommended Actions", "Follow-up Email"])

    # ── Transcript
    with tab_t:
        content = str(row.get("content", "No transcript available."))
        formatted = content.replace("**Sales Rep**", "🎙 Sales Rep").replace("**Customer**", "👤 Customer")
        st.markdown(f'<div class="transcript-box">{formatted}</div>', unsafe_allow_html=True)

    # ── AI Insights
    with tab_i:
        i1, i2 = st.columns(2)
        with i1:
            st.markdown(f"""
            <div class="detail-panel">
                <div class="detail-label">Summary</div>
                <div class="detail-value">{row.get('summary', '—')}</div>
            </div>
            <div class="detail-panel">
                <div class="detail-label">Sentiment Arc</div>
                <div class="detail-value">{row.get('sentiment_arc', '—')}</div>
            </div>
            <div class="detail-panel">
                <div class="detail-label">Key Issue</div>
                <div class="detail-value">{row.get('key_issue', '—')}</div>
            </div>
            """, unsafe_allow_html=True)
        with i2:
            st.markdown(f"""
            <div class="detail-panel">
                <div class="detail-label">Top Objection</div>
                <div class="detail-value">{row.get('top_objection', '—')}</div>
            </div>
            <div class="detail-panel">
                <div class="detail-label">Sales Outcome</div>
                <div class="detail-value">{row.get('outcome', '—')}</div>
            </div>
            <div class="detail-panel">
                <div class="detail-label">Rep Performance</div>
                {score_dots(int(row.get('rep_score', 0)))}
                <div class="detail-value" style="margin-top:0.4rem;">{row.get('rep_score_reason', '—')}</div>
            </div>
            """, unsafe_allow_html=True)
        quote = row.get("standout_quote", "")
        if quote and quote != "—":
            st.markdown(f'<div class="standout-quote">"{quote}"</div>', unsafe_allow_html=True)

    # ── Recommended Actions
    with tab_a:
        next_step = row.get("next_step", "")
        if next_step:
            st.markdown(f"""
            <div class="detail-panel" style="border-left: 3px solid {COLORS['accent']};">
                <div class="detail-label">Immediate Next Step</div>
                <div class="detail-value" style="font-weight:600; color:{COLORS['accent']};">{next_step}</div>
            </div>
            """, unsafe_allow_html=True)

        actions = row.get("recommended_actions", [])
        if isinstance(actions, str):
            try:
                import json as _json
                actions = _json.loads(actions)
            except Exception:
                actions = [actions]
        if actions:
            st.markdown(f'<div class="detail-panel">', unsafe_allow_html=True)
            st.markdown('<div class="detail-label">Action Items</div>', unsafe_allow_html=True)
            actions_html = ""
            for i, action in enumerate(actions, 1):
                actions_html += f'<div class="action-item"><div class="action-num">{i}</div><div>{action}</div></div>'
            st.markdown(actions_html + "</div>", unsafe_allow_html=True)

    # ── Email
    with tab_e:
        email_key = f"email_{selected_id}"
        if email_key not in st.session_state:
            st.session_state[email_key] = None

        if st.session_state[email_key] is None:
            st.markdown(f'<div style="font-size:0.85rem; color:{COLORS["text_muted"]}; margin-bottom:1rem;">Generate a personalized follow-up email based on the call content.</div>', unsafe_allow_html=True)
            _, btn_col, _ = st.columns([2, 3, 2])
            with btn_col:
                if st.button("Generate Follow-up Email", key=f"gen_email_{selected_id}"):
                    with st.spinner("Writing email..."):
                        email = generate_email(
                            summary=str(row.get("summary", "")),
                            key_issue=str(row.get("key_issue", "")),
                            next_step=str(row.get("next_step", "")),
                            sentiment=str(row.get("sentiment", "")),
                            transcript_excerpt=str(row.get("content", ""))[:800],
                        )
                    st.session_state[email_key] = email
                    st.rerun()
        else:
            st.markdown(f'<div class="email-box">{st.session_state[email_key]}</div>', unsafe_allow_html=True)
            c_copy, c_regen, _ = st.columns([2, 2, 4])
            with c_copy:
                st.code(st.session_state[email_key], language=None)
            with c_regen:
                if st.button("Regenerate", key=f"regen_{selected_id}"):
                    st.session_state[email_key] = None
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# FULL DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def render_dashboard():
    df = st.session_state.results_df
    total_available = st.session_state.total_available
    source_label = st.session_state.source_label

    # Header row
    h1, h2 = st.columns([6, 2])
    with h1:
        st.markdown(f"""
        <div style="margin-bottom:1.5rem;">
            <div style="font-family:'Sora',sans-serif; font-weight:700; font-size:1.3rem; color:{COLORS['text_primary']}; letter-spacing:-0.01em;">Dashboard</div>
            <div style="font-size:0.8rem; color:{COLORS['text_muted']}; margin-top:0.2rem;">{source_label}</div>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        if st.button("← New Analysis"):
            st.session_state.state = "empty"
            st.session_state.results_df = None
            st.cache_data.clear()
            st.rerun()

    render_kpis(df, total_available)
    st.markdown("<br>", unsafe_allow_html=True)
    render_charts(df)
    render_calls_table(df)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────────────────────────────────────
render_topbar()

state = st.session_state.state

if state == "empty":
    render_entry()

elif state == "processing":
    # We need the transcripts - re-fetch them. For sample, use cache.
    # For uploads, we've already lost the file — so we check source_label.
    if "upload" in st.session_state.source_label.lower():
        # Edge case: uploaded file lost on rerun — go back to entry
        st.warning("Please re-upload your file and click Analyze again.")
        st.session_state.state = "empty"
        st.rerun()
    else:
        with st.spinner("Fetching transcripts..."):
            transcripts = load_sample_transcripts()
        render_processing(transcripts)

elif state == "dashboard":
    if st.session_state.results_df is not None:
        render_dashboard()
    else:
        st.session_state.state = "empty"
        st.rerun()
