"""
CloseCall AI  —  Amazon India Customer Service Intelligence
==========================================================
Two-page app:
  Page 1 · Dashboard   — KPIs, charts, filterable call table
  Page 2 · Call Detail — per-call AI analysis, insights, next steps, follow-up email

Run:  streamlit run app.py
Requires: GROQ_API_KEY in environment  OR  .streamlit/secrets.toml  →  GROQ_API_KEY = "..."
"""

import os, json, textwrap
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CloseCall AI · Amazon India",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

XLSX_PATH  = "amazon_india_calls.xlsx"
GROQ_MODEL = "llama-3.3-70b-versatile"   # free, fast, multilingual

# ─────────────────────────────────────────────────────────────
# GROQ CLIENT
# ─────────────────────────────────────────────────────────────
def _groq():
    key = (
        os.environ.get("GROQ_API_KEY")
        or st.secrets.get("GROQ_API_KEY", "")
    )
    if not key:
        st.error("🔑 GROQ_API_KEY missing. Add it to `.streamlit/secrets.toml` or as an env var.")
        st.stop()
    return Groq(api_key=key)

# ─────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: #f5f4f1 !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }

/* Sidebar */
[data-testid="stSidebar"] { background: #0f0e0d !important; border-right: 1px solid #222 !important; }
[data-testid="stSidebar"] * { color: #777 !important; }
[data-testid="stSidebar"] span { color: #ccc !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div { background: #1a1917 !important; border-color: #2a2825 !important; }

/* Metric cards */
[data-testid="stMetric"] {
    background: white;
    border: 1.5px solid #e5e3dd;
    border-radius: 10px;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricLabel"] { font-size: 0.65rem !important; font-weight: 700 !important; color: #888 !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 800 !important; color: #1c1a18 !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1.5px solid #e4e2dc !important; }
.stTabs [data-baseweb="tab"] { font-size: 0.82rem !important; font-weight: 500 !important; color: #888 !important; background: transparent !important; border-bottom: 2px solid transparent !important; margin-bottom: -1.5px !important; padding: 0.5rem 1rem !important; }
.stTabs [aria-selected="true"] { color: #1d4ed8 !important; border-bottom-color: #1d4ed8 !important; }

/* Buttons */
.stButton > button {
    background: #1d4ed8 !important; color: white !important; border: none !important;
    border-radius: 7px !important; font-weight: 600 !important; font-size: 0.84rem !important;
    padding: 0.6rem 1.4rem !important; width: 100% !important;
    transition: background 0.15s !important;
}
.stButton > button:hover { background: #1e40af !important; }

/* Inputs */
div[data-testid="stTextInput"] input, div[data-baseweb="select"] > div {
    border-radius: 7px !important; border: 1.5px solid #e4e2dc !important;
    background: white !important; font-size: 0.875rem !important;
}

/* Progress */
.stProgress > div { background: #e4e2dc !important; height: 6px !important; border-radius: 99px !important; }
.stProgress > div > div { background: #1d4ed8 !important; border-radius: 99px !important; }

/* Spinner */
.stSpinner > div { border-top-color: #1d4ed8 !important; }

div[data-testid="stAlert"] { border-radius: 8px !important; font-size: 0.83rem !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# COLUMN MAP
# ─────────────────────────────────────────────────────────────
COL_MAP = {
    "Call ID":                 "id",
    "Timestamp":               "timestamp",
    "Duration (sec)":          "duration_sec",
    "Hold Time (sec)":         "hold_sec",
    "Channel":                 "channel",
    "Call Type":               "call_type",
    "Customer ID":             "customer_id",
    "Customer Name":           "customer_name",
    "Phone Number":            "phone",
    "City":                    "city",
    "State":                   "state",
    "Country":                 "country",
    "Customer Service Agent":  "agent_name",
    "Employee ID":             "employee_id",
    "Agent Experience (Yrs)":  "agent_exp",
    "Product ID":              "product_id",
    "Product Name":            "product_name",
    "Product Category":        "product_category",
    "Sentiment":               "sentiment",
    "Resolution":              "resolution",
    "First Call Resolution":   "fcr",
    "Transfers":               "transfers",
    "CSAT Score (1-5)":        "csat",
    "Transcript":              "content",
}

# ─────────────────────────────────────────────────────────────
# DATA LOADER
# ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if not os.path.exists(XLSX_PATH):
        st.error(f"❌ Dataset not found: `{XLSX_PATH}` — place it in the same folder as app.py")
        st.stop()
    df = pd.read_excel(XLSX_PATH, sheet_name="Call Records", engine="openpyxl")
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns=COL_MAP)
    df["sentiment"]  = df["sentiment"].astype(str).str.strip().str.title()
    df["call_type"]  = df["call_type"].astype(str).str.strip().str.title()
    df["resolution"] = df["resolution"].astype(str).str.strip().str.title()
    df["csat"]       = pd.to_numeric(df["csat"], errors="coerce")
    df["duration_sec"] = pd.to_numeric(df["duration_sec"], errors="coerce")
    return df

# ─────────────────────────────────────────────────────────────
# AI HELPERS
# ─────────────────────────────────────────────────────────────
ANALYSIS_PROMPT = """You are a senior customer-service quality analyst for Amazon India.
Analyse the support call transcript below. Return ONLY valid JSON — no markdown, no backticks.

{{
  "summary": "<2 sentences: what happened and how it ended>",
  "sentiment_arc": "<1 sentence: how the customer's mood shifted>",
  "key_issue": "<1 sentence: the root problem>",
  "resolution_quality": "<one of: Excellent, Good, Partial, Poor, Unresolved>",
  "agent_score": <1-5 integer>,
  "agent_score_reason": "<1 sentence>",
  "customer_risk": "<one of: Loyal, At Risk, Churned>",
  "top_objection": "<main friction point, or None>",
  "next_steps": ["<step 1>", "<step 2>", "<step 3>"],
  "standout_quote": "<most revealing customer line>",
  "tags": ["<tag1>", "<tag2>", "<tag3>"]
}}

Language note: transcript may be in Hindi, Hinglish, or English — analyse regardless.
Transcript:
{transcript}"""

EMAIL_PROMPT = """You are an Amazon India Customer Service representative writing a follow-up email.

Rules:
- Address the customer by first name
- Reference the exact product and issue from the call
- Confirm any refund / replacement / next step promised
- Warm, professional tone — not robotic
- Maximum 160 words
- No filler openers like "I hope this email finds you well"
- English only
- Return ONLY the email body (no subject line)

Customer first name: {first_name}
Product: {product}
Call type: {call_type}
Issue: {key_issue}
Resolution: {resolution}
Next step promised: {next_step}
Agent name: {agent_name}
Call reference: {call_id}"""


@st.cache_data(show_spinner=False)
def analyse_call(transcript: str, call_id: str) -> dict:
    try:
        resp = _groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": ANALYSIS_PROMPT.format(transcript=transcript[:3000])}],
            temperature=0.1,
            max_tokens=700,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        return {
            "summary": "Analysis unavailable — check API key.",
            "sentiment_arc": str(e), "key_issue": "—",
            "resolution_quality": "—", "agent_score": 0,
            "agent_score_reason": "—", "customer_risk": "—",
            "top_objection": "—", "next_steps": [],
            "standout_quote": "—", "tags": [],
        }


@st.cache_data(show_spinner=False)
def generate_email(first_name, product, call_type, key_issue,
                   resolution, next_step, agent_name, call_id) -> str:
    try:
        resp = _groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": EMAIL_PROMPT.format(
                first_name=first_name, product=product, call_type=call_type,
                key_issue=key_issue, resolution=resolution, next_step=next_step,
                agent_name=agent_name, call_id=call_id,
            )}],
            temperature=0.4,
            max_tokens=350,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not generate email: {e}"


# ─────────────────────────────────────────────────────────────
# UI PRIMITIVES
# ─────────────────────────────────────────────────────────────
SENT_CLR = {
    "Positive": ("#166534", "#f0fdf4"),
    "Negative": ("#991b1b", "#fef2f2"),
    "Very Negative": ("#7f1d1d", "#fef2f2"),
    "Mixed":    ("#92400e", "#fffbeb"),
    "Neutral":  ("#374151", "#f3f4f6"),
}
RES_CLR = {
    "Resolved":           ("#166534", "#f0fdf4"),
    "Refund Issued":      ("#166534", "#f0fdf4"),
    "Replacement Sent":   ("#0369a1", "#eff6ff"),
    "Partial Resolution": ("#92400e", "#fffbeb"),
    "Escalated":          ("#991b1b", "#fef2f2"),
    "Unresolved":         ("#991b1b", "#fef2f2"),
}
RISK_CLR = {
    "Loyal":    ("#166534", "#f0fdf4"),
    "At Risk":  ("#92400e", "#fffbeb"),
    "Churned":  ("#991b1b", "#fef2f2"),
}

def _pill(text, fg, bg):
    return (f'<span style="background:{bg};color:{fg};border-radius:4px;padding:2px 9px;'
            f'font-size:0.68rem;font-weight:700;letter-spacing:0.05em;'
            f'text-transform:uppercase;display:inline-block;">{text}</span>')

def sent_pill(v):
    fg, bg = SENT_CLR.get(v, ("#374151","#f3f4f6"))
    return _pill(v, fg, bg)

def res_pill(v):
    fg, bg = RES_CLR.get(v, ("#374151","#f3f4f6"))
    return _pill(v, fg, bg)

def risk_pill(v):
    fg, bg = RISK_CLR.get(v, ("#374151","#f3f4f6"))
    return _pill(v, fg, bg)

def csat_stars(v):
    try: n = int(v)
    except: return "—"
    filled = "★" * n
    empty  = "☆" * (5 - n)
    color  = "#166534" if n >= 4 else ("#92400e" if n == 3 else "#991b1b")
    return f'<span style="color:{color};font-size:1rem;">{filled}{empty}</span>'

def score_dots(n):
    try: n = int(n)
    except: n = 0
    dots = ""
    for i in range(1, 6):
        c = "#1d4ed8" if i <= n else "#e4e2dc"
        dots += f'<span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:{c};margin-right:3px;"></span>'
    return dots

def info_card(label, value, accent="#1d4ed8"):
    return f"""<div style="background:white;border:1.5px solid #e5e3dd;border-top:3px solid {accent};
border-radius:10px;padding:1rem 1.2rem;margin-bottom:0.6rem;">
<div style="font-size:0.6rem;font-weight:700;color:#888;text-transform:uppercase;
letter-spacing:0.1em;margin-bottom:0.3rem;">{label}</div>
<div style="font-size:0.88rem;color:#1c1a18;line-height:1.6;">{value}</div></div>"""

def section_header(text, sub=""):
    sub_html = f'<div style="font-size:0.75rem;color:#888;margin-top:0.2rem;">{sub}</div>' if sub else ""
    return f"""<div style="margin-bottom:1.1rem;padding-bottom:0.7rem;border-bottom:1.5px solid #e5e3dd;">
<div style="font-size:1rem;font-weight:700;color:#1c1a18;">{text}</div>{sub_html}</div>"""

def _safe(row, col, default="—"):
    v = row.get(col, default)
    return str(v) if v not in (None, "", float("nan"), "nan") else default


# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
def _init():
    defaults = {"page": "dashboard", "selected_call_id": None}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
def render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.markdown("""
        <div style="padding:1.6rem 1.2rem 1.2rem;border-bottom:1px solid #222;margin-bottom:1.2rem;">
          <div style="font-size:1.55rem;font-weight:800;color:#f0ede8;letter-spacing:-0.03em;">
            Close<span style="color:#5b8def;">Call</span>
          </div>
          <div style="font-size:0.6rem;font-weight:700;color:#333;text-transform:uppercase;
            letter-spacing:0.16em;margin-top:0.3rem;">Amazon India · AI Intelligence</div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown('<div style="font-size:0.6rem;font-weight:700;color:#333;text-transform:uppercase;letter-spacing:0.14em;padding:0 0.2rem;margin-bottom:0.5rem;">Navigate</div>', unsafe_allow_html=True)
        if st.button("📊  Dashboard", key="nav_dash"):
            st.session_state["page"] = "dashboard"
            st.rerun()
        if st.button("🔍  Call Detail", key="nav_detail"):
            st.session_state["page"] = "detail"
            st.rerun()

        st.markdown('<hr style="border-color:#222;margin:1rem 0;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.6rem;font-weight:700;color:#333;text-transform:uppercase;letter-spacing:0.14em;padding:0 0.2rem;margin-bottom:0.6rem;">Filters</div>', unsafe_allow_html=True)

        def opts(col):
            return sorted(df[col].dropna().astype(str).unique().tolist())

        sel_sent = st.multiselect("Sentiment",        opts("sentiment"),        default=opts("sentiment"),        key="f_sent")
        sel_res  = st.multiselect("Resolution",       opts("resolution"),       default=opts("resolution"),       key="f_res")
        sel_ct   = st.multiselect("Call Type",        opts("call_type"),        default=opts("call_type"),        key="f_ct")
        sel_cat  = st.multiselect("Product Category", opts("product_category"), default=opts("product_category"), key="f_cat")
        sel_st   = st.multiselect("State",            opts("state"),            default=opts("state"),            key="f_st")
        sel_ch   = st.multiselect("Channel",          opts("channel"),          default=opts("channel"),          key="f_ch")

        if st.button("Reset Filters", key="reset"):
            for k in ["f_sent","f_res","f_ct","f_cat","f_st","f_ch"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown(f'<div style="padding:0.8rem 0.2rem;font-size:0.68rem;color:#333;line-height:1.8;">'
                    f'Model: LLaMA 3.3 70B · Groq<br>Dataset: Amazon India · 50 calls</div>',
                    unsafe_allow_html=True)

    filtered = df.copy()
    if sel_sent: filtered = filtered[filtered["sentiment"].isin(sel_sent)]
    if sel_res:  filtered = filtered[filtered["resolution"].isin(sel_res)]
    if sel_ct:   filtered = filtered[filtered["call_type"].isin(sel_ct)]
    if sel_cat:  filtered = filtered[filtered["product_category"].isin(sel_cat)]
    if sel_st:   filtered = filtered[filtered["state"].isin(sel_st)]
    if sel_ch:   filtered = filtered[filtered["channel"].isin(sel_ch)]
    return filtered


# ─────────────────────────────────────────────────────────────
# PAGE 1 · DASHBOARD
# ─────────────────────────────────────────────────────────────
def render_dashboard(df: pd.DataFrame, df_all: pd.DataFrame):
    n        = len(df)
    n_all    = len(df_all)
    note     = f" (filtered: {n} of {n_all})" if n < n_all else f" · {n} calls"
    pos_pct  = round(len(df[df["sentiment"]=="Positive"]) / n * 100) if n else 0
    neg_pct  = round(len(df[df["sentiment"].isin(["Negative","Very Negative"])]) / n * 100) if n else 0
    avg_csat = df["csat"].mean()
    avg_dur  = df["duration_sec"].mean()
    esc      = len(df[df["resolution"]=="Escalated"])
    fcr_pct  = round(df[df["fcr"].astype(str).str.lower()=="yes"].shape[0] / n * 100) if n else 0

    # ── Header ────────────────────────────────────────────────
    st.markdown(f"""
    <div style="padding:1.6rem 0 1.4rem;border-bottom:1.5px solid #e5e3dd;margin-bottom:1.8rem;">
      <div style="font-size:1.8rem;font-weight:800;color:#1c1a18;letter-spacing:-0.03em;">
        CloseCall <span style="color:#1d4ed8;">Dashboard</span>
      </div>
      <div style="font-size:0.75rem;color:#888;margin-top:0.25rem;">
        Amazon India Customer Support Intelligence{note}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row ───────────────────────────────────────────────
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("📞 Calls",          str(n))
    k2.metric("😊 Positive",       f"{pos_pct}%")
    k3.metric("😡 Negative/Mixed", f"{neg_pct}%")
    k4.metric("⭐ Avg CSAT",       f"{avg_csat:.1f}/5" if n else "—")
    k5.metric("✅ FCR",            f"{fcr_pct}%")
    k6.metric("🚨 Escalated",      str(esc))

    st.markdown(f'<div style="font-size:0.72rem;color:#aaa;margin:0.4rem 0 1.8rem;">⏱ Avg call duration: <b style="color:#555;">{int(avg_dur)}s</b> &nbsp;·&nbsp; Avg hold: <b style="color:#555;">{int(df["hold_sec"].mean())}s</b></div>', unsafe_allow_html=True)

    # ── Charts row 1: Sentiment donut + Call Type bar ─────────
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div style="background:white;border:1.5px solid #e5e3dd;border-radius:10px;padding:1.2rem 1.4rem 0;">'
                    '<div style="font-size:0.85rem;font-weight:700;color:#1c1a18;">Sentiment Distribution</div>'
                    '<div style="font-size:0.72rem;color:#888;margin-bottom:0.4rem;">How customers felt across all calls</div>'
                    '</div>', unsafe_allow_html=True)
        sent = df["sentiment"].value_counts().reset_index()
        sent.columns = ["Sentiment","Count"]
        cmap = {"Positive":"#166534","Negative":"#dc2626","Very Negative":"#7f1d1d",
                "Mixed":"#d97706","Neutral":"#6b7280"}
        fig = px.pie(sent, names="Sentiment", values="Count", color="Sentiment",
                     color_discrete_map=cmap, hole=0.55)
        fig.update_traces(textinfo="percent+label", textfont_size=11,
                          marker=dict(line=dict(color="#fff",width=2)))
        fig.update_layout(showlegend=False, margin=dict(l=0,r=0,t=10,b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="Inter"))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    with c2:
        st.markdown('<div style="background:white;border:1.5px solid #e5e3dd;border-radius:10px;padding:1.2rem 1.4rem 0;">'
                    '<div style="font-size:0.85rem;font-weight:700;color:#1c1a18;">Call Type Breakdown</div>'
                    '<div style="font-size:0.72rem;color:#888;margin-bottom:0.4rem;">What customers are calling about</div>'
                    '</div>', unsafe_allow_html=True)
        ct = df["call_type"].value_counts().reset_index()
        ct.columns = ["Call Type","Count"]
        fig2 = px.bar(ct.head(10), x="Count", y="Call Type", orientation="h",
                      color="Count", color_continuous_scale=["#bfdbfe","#1d4ed8"],
                      text="Count")
        fig2.update_traces(textposition="outside", marker_line_width=0, textfont_size=10)
        fig2.update_layout(showlegend=False, coloraxis_showscale=False,
                           yaxis=dict(autorange="reversed", title=None),
                           xaxis=dict(title=None, gridcolor="#f0ede8"),
                           margin=dict(l=8,r=30,t=10,b=8),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font=dict(family="Inter",color="#888",size=11))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

    # ── Charts row 2: CSAT by category + Resolution mix ──────
    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<div style="background:white;border:1.5px solid #e5e3dd;border-radius:10px;padding:1.2rem 1.4rem 0;">'
                    '<div style="font-size:0.85rem;font-weight:700;color:#1c1a18;">Avg CSAT by Product Category</div>'
                    '<div style="font-size:0.72rem;color:#888;margin-bottom:0.4rem;">Which categories have the happiest customers</div>'
                    '</div>', unsafe_allow_html=True)
        csat_cat = df.groupby("product_category")["csat"].mean().reset_index().sort_values("csat")
        csat_cat.columns = ["Category","Avg CSAT"]
        fig3 = px.bar(csat_cat, x="Avg CSAT", y="Category", orientation="h",
                      color="Avg CSAT", color_continuous_scale=["#fca5a5","#166534"],
                      range_color=[1,5], text=csat_cat["Avg CSAT"].round(1))
        fig3.update_traces(textposition="outside", marker_line_width=0, textfont_size=10)
        fig3.update_layout(showlegend=False, coloraxis_showscale=False,
                           xaxis=dict(range=[0,5.5], title=None, gridcolor="#f0ede8"),
                           yaxis=dict(title=None),
                           margin=dict(l=8,r=30,t=10,b=8),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font=dict(family="Inter",color="#888",size=11))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})

    with c4:
        st.markdown('<div style="background:white;border:1.5px solid #e5e3dd;border-radius:10px;padding:1.2rem 1.4rem 0;">'
                    '<div style="font-size:0.85rem;font-weight:700;color:#1c1a18;">Resolution Outcomes</div>'
                    '<div style="font-size:0.72rem;color:#888;margin-bottom:0.4rem;">How calls were resolved</div>'
                    '</div>', unsafe_allow_html=True)
        res = df["resolution"].value_counts().reset_index()
        res.columns = ["Resolution","Count"]
        rcmap = {"Resolved":"#166534","Refund Issued":"#0369a1","Replacement Sent":"#0891b2",
                 "Partial Resolution":"#d97706","Escalated":"#dc2626","Unresolved":"#991b1b"}
        fig4 = px.bar(res, x="Resolution", y="Count", color="Resolution",
                      color_discrete_map=rcmap, text="Count")
        fig4.update_traces(textposition="outside", marker_line_width=0, textfont_size=11)
        fig4.update_layout(showlegend=False, xaxis=dict(title=None, gridcolor="#f0ede8"),
                           yaxis=dict(title=None, gridcolor="#f0ede8"),
                           margin=dict(l=8,r=8,t=10,b=8),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font=dict(family="Inter",color="#888",size=11))
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar":False})

    # ── Agent leaderboard ─────────────────────────────────────
    st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.85rem;font-weight:700;color:#1c1a18;margin-bottom:0.8rem;">Agent Leaderboard</div>', unsafe_allow_html=True)

    agent_stats = (
        df.groupby("agent_name")
        .agg(calls=("id","count"), avg_csat=("csat","mean"),
             neg_calls=("sentiment", lambda x: (x.isin(["Negative","Very Negative"])).sum()),
             fcr_yes=("fcr", lambda x: (x.astype(str).str.lower()=="yes").sum()))
        .reset_index()
    )
    agent_stats["fcr_pct"]   = (agent_stats["fcr_yes"] / agent_stats["calls"] * 100).round(0).astype(int)
    agent_stats["avg_csat"]  = agent_stats["avg_csat"].round(2)
    agent_stats["neg_pct"]   = (agent_stats["neg_calls"] / agent_stats["calls"] * 100).round(0).astype(int)
    agent_stats = agent_stats.sort_values("avg_csat", ascending=False)

    th_style = "padding:9px 14px;text-align:left;font-size:0.6rem;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:0.08em;white-space:nowrap;"
    td_style = "padding:10px 14px;font-size:0.82rem;color:#4a4642;border-bottom:1px solid #f5f4f1;"

    rows_html = ""
    for _, a in agent_stats.iterrows():
        csat_v = a["avg_csat"]
        csat_clr = "#166534" if csat_v >= 4 else ("#d97706" if csat_v >= 3 else "#dc2626")
        rows_html += f"""
        <tr>
          <td style="{td_style}font-weight:600;color:#1c1a18;">{a['agent_name']}</td>
          <td style="{td_style}text-align:center;">{a['calls']}</td>
          <td style="{td_style}text-align:center;font-weight:700;color:{csat_clr};">{csat_v:.2f}</td>
          <td style="{td_style}text-align:center;">{a['fcr_pct']}%</td>
          <td style="{td_style}text-align:center;color:#dc2626;">{a['neg_pct']}%</td>
        </tr>"""

    st.markdown(f"""
    <div style="background:white;border:1.5px solid #e5e3dd;border-radius:10px;overflow:hidden;margin-bottom:2rem;">
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr style="background:#faf9f7;border-bottom:1.5px solid #e5e3dd;">
          <th style="{th_style}">Agent</th>
          <th style="{th_style}text-align:center;">Calls</th>
          <th style="{th_style}text-align:center;">Avg CSAT</th>
          <th style="{th_style}text-align:center;">FCR %</th>
          <th style="{th_style}text-align:center;">Neg %</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

    # ── Calls table ───────────────────────────────────────────
    st.markdown('<div style="font-size:0.85rem;font-weight:700;color:#1c1a18;margin-bottom:0.6rem;">All Calls</div>', unsafe_allow_html=True)
    search_col, _ = st.columns([4, 5])
    with search_col:
        q = st.text_input("", placeholder="🔍  Search by customer, product, city, call type…",
                          label_visibility="collapsed", key="dash_search")

    fdf = df.copy()
    if q:
        mask = pd.Series(False, index=fdf.index)
        for col in ["id","customer_name","product_name","city","state","call_type","agent_name","channel"]:
            mask |= fdf[col].astype(str).str.contains(q, case=False, na=False)
        fdf = fdf[mask]

    st.markdown(f'<div style="font-size:0.7rem;color:#aaa;margin-bottom:0.5rem;">{len(fdf)} calls</div>', unsafe_allow_html=True)

    rows_html = ""
    for _, r in fdf.head(50).iterrows():
        cid = _safe(r,"id")
        rows_html += f"""
        <tr style="border-bottom:1px solid #f5f4f1;cursor:pointer;"
            onclick="window.location.href='?'">
          <td style="{td_style}font-weight:600;white-space:nowrap;">{cid}</td>
          <td style="{td_style}">{_safe(r,'customer_name')}<br>
            <span style="font-size:0.68rem;color:#aaa;">{_safe(r,'city')}, {_safe(r,'state')}</span></td>
          <td style="{td_style}max-width:180px;">{_safe(r,'product_name')[:40]}</td>
          <td style="{td_style}">{_safe(r,'call_type')}</td>
          <td style="{td_style}">{sent_pill(_safe(r,'sentiment','Neutral'))}</td>
          <td style="{td_style}">{res_pill(_safe(r,'resolution','—'))}</td>
          <td style="{td_style}">{csat_stars(r.get('csat'))}</td>
          <td style="{td_style}">{_safe(r,'agent_name')}</td>
        </tr>"""

    th = "".join(f'<th style="{th_style}">{h}</th>'
                 for h in ["Call ID","Customer","Product","Call Type","Sentiment","Resolution","CSAT","Agent"])
    st.markdown(f"""
    <div style="background:white;border:1.5px solid #e5e3dd;border-radius:10px;
      overflow:hidden;overflow-x:auto;margin-bottom:2rem;">
      <table style="width:100%;border-collapse:collapse;font-size:0.82rem;">
        <thead><tr style="background:#faf9f7;border-bottom:1.5px solid #e5e3dd;">{th}</tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

    # ── Jump to detail ─────────────────────────────────────────
    st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#1c1a18;margin-bottom:0.5rem;">Open a call in Detail View</div>', unsafe_allow_html=True)
    jump_col, btn_col, _ = st.columns([4, 2, 3])
    with jump_col:
        sel_id = st.selectbox("", fdf["id"].tolist(), label_visibility="collapsed", key="jump_id")
    with btn_col:
        if st.button("Open Call →", key="open_call"):
            st.session_state["selected_call_id"] = sel_id
            st.session_state["page"] = "detail"
            st.rerun()


# ─────────────────────────────────────────────────────────────
# PAGE 2 · CALL DETAIL
# ─────────────────────────────────────────────────────────────
def render_detail(df: pd.DataFrame):
    st.markdown("""
    <div style="padding:1.6rem 0 1.4rem;border-bottom:1.5px solid #e5e3dd;margin-bottom:1.8rem;">
      <div style="font-size:1.8rem;font-weight:800;color:#1c1a18;letter-spacing:-0.03em;">
        Call <span style="color:#1d4ed8;">Detail</span>
      </div>
      <div style="font-size:0.75rem;color:#888;margin-top:0.25rem;">
        AI analysis · next steps · follow-up email
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Call selector ─────────────────────────────────────────
    sel_col, _ = st.columns([5, 4])
    with sel_col:
        default_id = st.session_state.get("selected_call_id") or df["id"].iloc[0]
        if default_id not in df["id"].values:
            default_id = df["id"].iloc[0]
        idx = df["id"].tolist().index(default_id)
        sel_id = st.selectbox(
            "Select call",
            df["id"].tolist(),
            index=idx,
            format_func=lambda cid: (
                lambda row: f"{cid}  ·  {_safe(row,'customer_name')}  ·  {_safe(row,'product_name')[:35]}  ·  {_safe(row,'city')}"
            )(df[df["id"]==cid].iloc[0]) if not df[df["id"]==cid].empty else cid,
            key="detail_sel",
        )

    r = df[df["id"] == sel_id].iloc[0]

    # ── Meta strip ────────────────────────────────────────────
    def meta_chip(label, val):
        return (f'<span style="display:inline-flex;align-items:center;gap:5px;background:white;'
                f'border:1.5px solid #e5e3dd;border-radius:6px;padding:4px 11px;'
                f'font-size:0.7rem;color:#888;">'
                f'<b style="color:#1c1a18;">{label}</b> {val}</span>')

    dur  = r.get("duration_sec","")
    hold = r.get("hold_sec","")
    dur_s  = f"{int(dur)//60}m {int(dur)%60}s"  if dur  and str(dur)  != "nan" else "—"
    hold_s = f"{int(hold)}s"                      if hold and str(hold) != "nan" else "—"

    st.markdown(f"""<div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1.2rem;">
      {meta_chip("📅", _safe(r,"timestamp"))}
      {meta_chip("📞", _safe(r,"channel"))}
      {meta_chip("⏱", dur_s)}
      {meta_chip("⏸ Hold", hold_s)}
      {meta_chip("👤 Agent", _safe(r,"agent_name"))}
      {meta_chip("🆔 EmpID", _safe(r,"employee_id"))}
      {meta_chip("📦", _safe(r,"product_name")[:40])}
      {meta_chip("🗂", _safe(r,"product_category"))}
      {meta_chip("📍", _safe(r,"city") + ", " + _safe(r,"state"))}
    </div>""", unsafe_allow_html=True)

    # ── Quick-status row ──────────────────────────────────────
    q1,q2,q3,q4 = st.columns(4)
    sfg, sbg = SENT_CLR.get(_safe(r,"sentiment"), ("#374151","#f3f4f6"))
    rfg, rbg = RES_CLR.get(_safe(r,"resolution"), ("#374151","#f3f4f6"))

    def status_card(label, value, fg, bg):
        return f"""<div style="background:{bg};border-radius:8px;padding:0.9rem 1.1rem;">
          <div style="font-size:0.6rem;font-weight:700;color:{fg}80;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.2rem;">{label}</div>
          <div style="font-size:0.9rem;font-weight:700;color:{fg};">{value}</div></div>"""

    with q1: st.markdown(status_card("Sentiment",   _safe(r,"sentiment"),   sfg, sbg), unsafe_allow_html=True)
    with q2: st.markdown(status_card("Resolution",  _safe(r,"resolution"),  rfg, rbg), unsafe_allow_html=True)
    with q3: st.markdown(status_card("Dataset CSAT",f"★ {_safe(r,'csat')}/5","#1c1a18","#faf9f7"), unsafe_allow_html=True)
    with q4: st.markdown(status_card("Transfers",   _safe(r,"transfers"),   "#1c1a18","#faf9f7"), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📄  Transcript", "🧠  AI Analysis", "✅  Next Steps", "✉️  Follow-up Email"])

    # ── TAB 1: Transcript ─────────────────────────────────────
    with tab1:
        transcript = str(r.get("content","No transcript available."))
        display = (transcript
            .replace("Agent:",        "<strong style='color:#1d4ed8;'>🎙 Agent:</strong>")
            .replace("Senior Agent:", "<strong style='color:#7c3aed;'>🎙 Sr Agent:</strong>")
            .replace("Supervisor:",   "<strong style='color:#7c3aed;'>🎙 Supervisor:</strong>")
            .replace("Customer:",     "<strong style='color:#166534;'>👤 Customer:</strong>")
            .replace("\n","<br>"))
        st.markdown(f"""
        <div style="background:#fafaf8;border:1.5px solid #e5e3dd;border-radius:10px;
          padding:1.4rem 1.8rem;font-size:0.83rem;color:#3a3a3a;line-height:2.1;
          max-height:420px;overflow-y:auto;">{display}</div>
        """, unsafe_allow_html=True)

    # ── TAB 2: AI Analysis ────────────────────────────────────
    with tab2:
        with st.spinner("Running AI analysis…"):
            ai = analyse_call(str(r.get("content","")), str(r.get("id","")))

        # Summary + arc
        st.markdown(info_card("📋 Call Summary", ai.get("summary","—"), "#1d4ed8"), unsafe_allow_html=True)
        st.markdown(info_card("📈 Sentiment Arc", ai.get("sentiment_arc","—"), "#0891b2"), unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(info_card("🔍 Root Issue",     ai.get("key_issue","—"),          "#d97706"), unsafe_allow_html=True)
            st.markdown(info_card("🚧 Top Objection",  ai.get("top_objection","—"),       "#dc2626"), unsafe_allow_html=True)
            st.markdown(info_card("📊 Resolution Quality", ai.get("resolution_quality","—"), "#0369a1"), unsafe_allow_html=True)
        with col_b:
            # Agent score with dots
            score_val = ai.get("agent_score", 0)
            st.markdown(f"""<div style="background:white;border:1.5px solid #e5e3dd;
              border-top:3px solid #7c3aed;border-radius:10px;padding:1rem 1.2rem;margin-bottom:0.6rem;">
              <div style="font-size:0.6rem;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">🤖 Agent Score</div>
              <div style="margin-bottom:0.35rem;">{score_dots(score_val)}</div>
              <div style="font-size:0.88rem;color:#1c1a18;line-height:1.6;">{ai.get('agent_score_reason','—')}</div>
            </div>""", unsafe_allow_html=True)

            # Customer risk
            risk_v = ai.get("customer_risk","—")
            rfg2, rbg2 = RISK_CLR.get(risk_v, ("#374151","#f3f4f6"))
            st.markdown(f"""<div style="background:{rbg2};border:1.5px solid #e5e3dd;
              border-top:3px solid {rfg2};border-radius:10px;padding:1rem 1.2rem;margin-bottom:0.6rem;">
              <div style="font-size:0.6rem;font-weight:700;color:{rfg2}80;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">🎯 Customer Risk</div>
              <div style="font-size:0.9rem;font-weight:700;color:{rfg2};">{risk_v}</div>
            </div>""", unsafe_allow_html=True)

            # Tags
            tags = ai.get("tags", [])
            if tags:
                tag_html = " ".join(f'<span style="background:#eef2ff;color:#1d4ed8;border-radius:4px;padding:2px 8px;font-size:0.68rem;font-weight:600;margin-right:4px;">{t}</span>' for t in tags)
                st.markdown(f"""<div style="background:white;border:1.5px solid #e5e3dd;border-radius:10px;padding:1rem 1.2rem;">
                  <div style="font-size:0.6rem;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.4rem;">🏷 Tags</div>
                  <div>{tag_html}</div></div>""", unsafe_allow_html=True)

        # Standout quote
        q_text = ai.get("standout_quote","")
        if q_text and q_text != "—":
            st.markdown(f"""
            <div style="border-left:3px solid #1d4ed8;padding:0.8rem 1.2rem;background:#eef2ff;
              border-radius:0 8px 8px 0;font-style:italic;color:#374151;font-size:0.86rem;
              margin-top:0.4rem;">"{q_text}"</div>
            """, unsafe_allow_html=True)

    # ── TAB 3: Next Steps ─────────────────────────────────────
    with tab3:
        with st.spinner("Generating recommendations…"):
            ai3 = analyse_call(str(r.get("content","")), str(r.get("id","")))

        next_steps = ai3.get("next_steps", [])

        # Immediate action banner
        if next_steps:
            st.markdown(f"""
            <div style="background:#eef2ff;border:1.5px solid #bfdbfe;border-left:4px solid #1d4ed8;
              border-radius:0 10px 10px 0;padding:1rem 1.4rem;margin-bottom:1.2rem;">
              <div style="font-size:0.6rem;font-weight:700;color:#1d4ed8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.25rem;">🚀 Immediate Priority</div>
              <div style="font-size:0.92rem;font-weight:600;color:#1e3a8a;line-height:1.6;">{next_steps[0]}</div>
            </div>
            """, unsafe_allow_html=True)

        # Remaining steps
        if len(next_steps) > 1:
            items = ""
            for i, step in enumerate(next_steps[1:], 2):
                items += f"""
                <div style="display:flex;gap:0.75rem;align-items:flex-start;padding:0.8rem 0;
                  border-bottom:1px solid #f5f4f1;font-size:0.84rem;color:#1c1a18;line-height:1.6;">
                  <div style="min-width:24px;height:24px;background:#eef2ff;color:#1d4ed8;
                    font-weight:700;font-size:0.7rem;border-radius:50%;display:flex;
                    align-items:center;justify-content:center;flex-shrink:0;margin-top:2px;">{i}</div>
                  <div>{step}</div>
                </div>"""
            st.markdown(f"""
            <div style="background:white;border:1.5px solid #e5e3dd;border-radius:10px;
              padding:0.4rem 1.2rem 0.6rem;margin-bottom:1.2rem;">
              <div style="font-size:0.6rem;font-weight:700;color:#888;text-transform:uppercase;
                letter-spacing:0.1em;padding-top:0.8rem;margin-bottom:0.2rem;">Further Actions</div>
              {items}
            </div>
            """, unsafe_allow_html=True)

        # Insight panel — risk + quality + objection summary
        col_x, col_y = st.columns(2)
        with col_x:
            risk_v = ai3.get("customer_risk","—")
            rfg2, rbg2 = RISK_CLR.get(risk_v, ("#374151","#f3f4f6"))
            st.markdown(f"""
            <div style="background:{rbg2};border:1.5px solid #e5e3dd;border-radius:10px;padding:1rem 1.2rem;">
              <div style="font-size:0.6rem;font-weight:700;color:{rfg2}80;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Customer Risk Level</div>
              <div style="font-size:1.1rem;font-weight:800;color:{rfg2};">{risk_v}</div>
              <div style="font-size:0.78rem;color:{rfg2}90;margin-top:0.25rem;">
              {"⚠️ Flag for retention team" if risk_v in ("At Risk","Churned") else "✅ No immediate action needed"}</div>
            </div>""", unsafe_allow_html=True)
        with col_y:
            rq = ai3.get("resolution_quality","—")
            rq_clr = {"Excellent":"#166534","Good":"#0369a1","Partial":"#d97706",
                      "Poor":"#dc2626","Unresolved":"#991b1b"}.get(rq,"#374151")
            st.markdown(f"""
            <div style="background:white;border:1.5px solid #e5e3dd;border-radius:10px;padding:1rem 1.2rem;">
              <div style="font-size:0.6rem;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Resolution Quality</div>
              <div style="font-size:1.1rem;font-weight:800;color:{rq_clr};">{rq}</div>
              <div style="font-size:0.78rem;color:#888;margin-top:0.25rem;">{ai3.get('key_issue','—')[:80]}</div>
            </div>""", unsafe_allow_html=True)

    # ── TAB 4: Follow-up Email ────────────────────────────────
    with tab4:
        ek = f"email_{sel_id}"
        if ek not in st.session_state:
            st.session_state[ek] = None

        # Get AI data (cached — no extra API call)
        ai4 = analyse_call(str(r.get("content","")), str(r.get("id","")))

        first_name   = _safe(r,"customer_name").split()[0]
        product      = _safe(r,"product_name")
        call_type    = _safe(r,"call_type")
        resolution   = _safe(r,"resolution")
        agent        = _safe(r,"agent_name")
        next_step    = ai4.get("next_steps",["Follow up with customer"])[0]
        key_issue    = ai4.get("key_issue","—")
        call_id      = _safe(r,"id")

        # Preview card — shows what will be used
        st.markdown(f"""
        <div style="background:#fafaf8;border:1.5px solid #e5e3dd;border-radius:10px;
          padding:1.2rem 1.5rem;margin-bottom:1.2rem;">
          <div style="font-size:0.6rem;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.7rem;">📋 Email will be personalised with</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;font-size:0.8rem;">
            <div><span style="color:#888;">Customer:</span> <b style="color:#1c1a18;">{first_name}</b></div>
            <div><span style="color:#888;">Product:</span> <b style="color:#1c1a18;">{product[:35]}</b></div>
            <div><span style="color:#888;">Issue:</span> <b style="color:#1c1a18;">{key_issue[:50]}</b></div>
            <div><span style="color:#888;">Resolution:</span> <b style="color:#1c1a18;">{resolution}</b></div>
            <div><span style="color:#888;">Next step:</span> <b style="color:#1c1a18;">{next_step[:50]}</b></div>
            <div><span style="color:#888;">Call ref:</span> <b style="color:#1c1a18;">{call_id}</b></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state[ek] is None:
            _, btn_col, _ = st.columns([2,3,2])
            with btn_col:
                if st.button("✉️  Generate Follow-up Email", key=f"gen_{sel_id}"):
                    with st.spinner("Writing personalised email…"):
                        email_body = generate_email(
                            first_name=first_name,
                            product=product,
                            call_type=call_type,
                            key_issue=key_issue,
                            resolution=resolution,
                            next_step=next_step,
                            agent_name=agent,
                            call_id=call_id,
                        )
                    st.session_state[ek] = email_body
                    st.rerun()
        else:
            # Subject line suggestion
            subj = f"Re: Your recent Amazon support call — {product[:30]} [{call_id}]"
            st.markdown(f"""
            <div style="background:#eef2ff;border:1.5px solid #bfdbfe;border-radius:8px;
              padding:0.7rem 1.1rem;margin-bottom:0.8rem;font-size:0.82rem;">
              <span style="font-size:0.6rem;font-weight:700;color:#1d4ed8;text-transform:uppercase;letter-spacing:0.1em;">Suggested Subject Line</span><br>
              <b style="color:#1e3a8a;">{subj}</b>
            </div>
            """, unsafe_allow_html=True)

            # Email body
            st.markdown(f"""
            <div style="background:white;border:1.5px solid #e5e3dd;border-radius:10px;
              padding:1.4rem 1.8rem;font-size:0.88rem;color:#1c1a18;line-height:1.95;
              white-space:pre-wrap;margin-bottom:0.8rem;">{st.session_state[ek]}</div>
            """, unsafe_allow_html=True)

            # Copy-ready code block + regenerate
            col_copy, col_regen, _ = st.columns([3,2,4])
            with col_copy:
                st.code(st.session_state[ek], language=None)
            with col_regen:
                if st.button("🔄 Regenerate", key=f"regen_{sel_id}"):
                    st.session_state[ek] = None
                    # Clear cache for this specific call so we get a fresh response
                    generate_email.clear()
                    st.rerun()


# ─────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────
df_all    = load_data()
df_filtered = render_sidebar(df_all)

if st.session_state["page"] == "dashboard":
    render_dashboard(df_filtered, df_all)
else:
    render_detail(df_filtered if not df_filtered.empty else df_all)
