import json
import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_sample_transcripts, load_csv_transcripts
from analyzer import analyze_batch, generate_email

st.set_page_config(
    page_title="CloseCall · Sales Intelligence",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,500;0,600;1,500&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --bg:      #f6f5f2;
  --surface: #ffffff;
  --border:  #e4e2dc;
  --text:    #1c1a18;
  --muted:   #857f78;
  --subtle:  #c2bdb6;
  --accent:  #1d4ed8;
  --aclt:    #eef2ff;
  --acdk:    #1e40af;
  --green:   #166534;
  --greenlt: #f0fdf4;
  --red:     #991b1b;
  --redlt:   #fef2f2;
  --amber:   #92400e;
  --amberlt: #fffbeb;
}

*, html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: var(--bg) !important; }

#MainMenu, footer, header    { visibility: hidden; }
[data-testid="stToolbar"]    { display: none; }
[data-testid="stDecoration"] { display: none; }

[data-testid="stSidebar"] {
    background: #100f0e !important;
    border-right: 1px solid #232220 !important;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }
section[data-testid="stSidebar"] * { color: #6b6560 !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #1a1917 !important; border-color: #2a2825 !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] { background: #1d4ed8 !important; }
[data-testid="stSidebar"] span { color: #e4e2dc !important; }

.stButton > button {
    background: var(--accent) !important;
    color: #fff !important; border: none !important;
    border-radius: 7px !important; font-weight: 600 !important;
    font-size: 0.84rem !important; padding: 0.68rem 1.6rem !important;
    width: 100% !important;
    transition: background 0.12s, box-shadow 0.12s !important;
    box-shadow: 0 1px 3px rgba(29,78,216,0.18) !important;
}
.stButton > button:hover {
    background: var(--acdk) !important;
    box-shadow: 0 4px 16px rgba(29,78,216,0.28) !important;
}

.stProgress > div {
    background: #e4e2dc !important;
    border-radius: 99px !important; height: 6px !important;
}
.stProgress > div > div {
    background: var(--accent) !important; border-radius: 99px !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1.5px solid var(--border) !important; gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-weight: 500 !important; font-size: 0.81rem !important;
    color: var(--muted) !important; padding: 0.55rem 1.1rem !important;
    border-radius: 0 !important; background: transparent !important;
    border-bottom: 2px solid transparent !important; margin-bottom: -1.5px !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important; border-bottom-color: var(--accent) !important;
}

[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1.5px dashed var(--border) !important; border-radius: 10px !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }
[data-testid="stFileUploader"] section {
    background: transparent !important; border: none !important; padding: 1.4rem !important;
}
[data-testid="stFileUploader"] label { display: none !important; }

div[data-testid="stTextInput"] input {
    border-radius: 7px !important; border: 1.5px solid var(--border) !important;
    font-size: 0.875rem !important; background: var(--surface) !important;
    padding: 0.55rem 0.9rem !important; color: var(--text) !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(29,78,216,0.08) !important;
}
div[data-baseweb="select"] > div {
    border-radius: 7px !important; border: 1.5px solid var(--border) !important;
    background: var(--surface) !important; font-size: 0.875rem !important;
}
.stSpinner > div { border-top-color: var(--accent) !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────
DEFAULTS = {
    "stage": "home",
    "results_df": None,
    "total_fetched": 0,
    "source_label": "",
    "_pending_transcripts": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ────────────────────────────────────────────────────
SENT_COLORS = {
    "Positive": ("#166534", "#f0fdf4"),
    "Negative": ("#991b1b", "#fef2f2"),
    "Mixed":    ("#92400e", "#fffbeb"),
    "Neutral":  ("#4b5563", "#f3f4f6"),
}
RESOLUTION_COLORS = {
    "Resolved":           ("#166534", "#f0fdf4"),
    "Refund Issued":      ("#166534", "#f0fdf4"),
    "Replacement Sent":   ("#166534", "#f0fdf4"),
    "Escalated":          ("#991b1b", "#fef2f2"),
    "Unresolved":         ("#991b1b", "#fef2f2"),
    "Partial Resolution": ("#92400e", "#fffbeb"),
    "Callback Scheduled": ("#1e40af", "#eef2ff"),
    "Pending":            ("#1e40af", "#eef2ff"),
}

def pill(text, fg, bg):
    return (f'<span style="display:inline-block;background:{bg};color:{fg};'
            f'border-radius:4px;padding:2px 9px;font-size:0.68rem;font-weight:700;'
            f'letter-spacing:0.06em;text-transform:uppercase;">{text}</span>')

def sent_pill(v):
    fg, bg = SENT_COLORS.get(str(v), ("#4b5563", "#f3f4f6"))
    return pill(v, fg, bg)

def res_pill(v):
    fg, bg = RESOLUTION_COLORS.get(str(v), ("#4b5563", "#f3f4f6"))
    return pill(v, fg, bg)

def score_dots(n):
    try: n = int(n)
    except: n = 0
    html = ""
    for i in range(1, 6):
        c = "#1d4ed8" if i <= n else "#e4e2dc"
        html += f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{c};margin-right:3px;"></span>'
    return html

def _safe_list(df, col):
    if col not in df.columns:
        return []
    return sorted(df[col].dropna().astype(str).replace("", pd.NA).dropna().unique().tolist())

def _v(r, col, default="—"):
    v = r.get(col, default)
    return str(v) if v not in (None, "", float("nan")) else default

def _meta_chip(label_text, value):
    return (f'<span style="display:inline-flex;align-items:center;gap:4px;'
            f'background:var(--surface);border:1.5px solid var(--border);'
            f'border-radius:6px;padding:4px 10px;font-size:0.7rem;color:var(--muted);">'
            f'<span style="font-weight:600;color:var(--text);">{label_text}</span>'
            f'&nbsp;{value}</span>')

# ── FIX 1: Chart layout — no xaxis/yaxis in base, pass separately each time ──
def _chart_base():
    return dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#857f78", size=11),
        margin=dict(l=8, r=8, t=8, b=8),
    )

def _axes(grid="#f0ede8"):
    return dict(
        xaxis=dict(gridcolor=grid, zerolinecolor=grid, title=None),
        yaxis=dict(gridcolor=grid, zerolinecolor=grid, title=None),
    )

# ── Sidebar logo ───────────────────────────────────────────────
def _sidebar_logo(tagline="Customer Support Intelligence"):
    st.markdown(f"""
    <div style="padding:1.8rem 1.2rem 1.2rem;border-bottom:1px solid #232220;margin-bottom:1.4rem;">
      <div style="font-family:'Lora',serif;font-size:1.65rem;color:#f0ede8;letter-spacing:-0.02em;line-height:1.1;">
        Close<span style="color:#5b8def;">Call</span>
      </div>
      <div style="font-size:0.62rem;font-weight:600;color:#302e2c;text-transform:uppercase;letter-spacing:0.16em;margin-top:0.35rem;">
        {tagline}
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── HOME ───────────────────────────────────────────────────────
def render_home():
    with st.sidebar:
        _sidebar_logo()
        st.markdown("""
        <div style="padding:0 1.2rem;font-size:0.77rem;color:#4a4642;line-height:2.1;">
          <div>💬&nbsp; Spots customer objections &amp; root issues</div>
          <div>📊&nbsp; Tracks sentiment &amp; resolution rates</div>
          <div>⭐&nbsp; Scores agent performance per call</div>
          <div>✉️&nbsp; Writes follow-up emails automatically</div>
          <div>📋&nbsp; Recommends concrete next actions</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="padding:3.5rem 0 2.8rem;">
      <div style="display:inline-block;background:#eef2ff;color:#1d4ed8;
        font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;
        padding:4px 11px;border-radius:4px;margin-bottom:1.1rem;">
        AI · Customer Service Intelligence
      </div>
      <div style="font-family:'Lora',serif;font-size:3rem;color:#1c1a18;
        letter-spacing:-0.03em;line-height:1.12;margin-bottom:1rem;">
        Every call,<br><em style="color:#1d4ed8;">fully understood.</em>
      </div>
      <div style="font-size:0.97rem;color:#857f78;max-width:460px;line-height:1.8;">
        Drop in your customer service transcripts or try the sample dataset.
        CloseCall reads them, finds what matters, and tells your team exactly what to do next.
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_a, gap, col_b = st.columns([11, 1, 11])

    with col_a:
        st.markdown("""
        <div style="background:#fff;border:1.5px solid #e4e2dc;border-radius:12px;padding:1.8rem 1.8rem 1.2rem;">
          <div style="font-size:0.62rem;font-weight:700;color:#c2bdb6;text-transform:uppercase;letter-spacing:0.13em;margin-bottom:0.5rem;">Option A</div>
          <div style="font-size:1rem;font-weight:700;color:#1c1a18;margin-bottom:0.5rem;">Upload Your Transcripts</div>
          <div style="font-size:0.82rem;color:#857f78;line-height:1.75;margin-bottom:1.2rem;">
            Upload a <code style="background:#f6f5f2;padding:1px 5px;border-radius:3px;">.csv</code>
            with a <code style="background:#f6f5f2;padding:1px 5px;border-radius:3px;">transcript</code> column.
            Optional: <code style="background:#f6f5f2;padding:1px 5px;border-radius:3px;">id</code>,
            <code style="background:#f6f5f2;padding:1px 5px;border-radius:3px;">customer_name</code>.
          </div>
        </div>
        """, unsafe_allow_html=True)
        uploaded = st.file_uploader("upload_csv", type=["csv"], label_visibility="collapsed", key="csv_upload")
        if uploaded:
            if st.button("Analyze Uploaded Calls →", key="btn_upload"):
                try:
                    transcripts = load_csv_transcripts(uploaded)
                    _start_analysis(transcripts, f"{len(transcripts)} uploaded calls")
                except Exception as e:
                    st.error(f"CSV error: {e}")

    with gap:
        st.markdown("""
        <div style="display:flex;align-items:center;justify-content:center;height:240px;">
          <div style="position:relative;width:1px;height:100px;background:#e4e2dc;">
            <span style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
              background:#f6f5f2;color:#c2bdb6;font-size:0.68rem;font-weight:600;
              padding:5px 0;white-space:nowrap;">or</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div style="background:#fff;border:1.5px solid #e4e2dc;border-radius:12px;padding:1.8rem 1.8rem 1.2rem;">
          <div style="font-size:0.62rem;font-weight:700;color:#c2bdb6;text-transform:uppercase;letter-spacing:0.13em;margin-bottom:0.5rem;">Option B</div>
          <div style="font-size:1rem;font-weight:700;color:#1c1a18;margin-bottom:0.5rem;">Try the Sample Dataset</div>
          <div style="font-size:0.82rem;color:#857f78;line-height:1.75;margin-bottom:1.2rem;">
            100 sales call transcripts across fashion, real estate, finance, healthcare &amp; tech. No upload needed.
          </div>
          <div style="display:flex;gap:0.45rem;flex-wrap:wrap;margin-bottom:0.2rem;">
            <span style="background:#eef2ff;color:#1d4ed8;border-radius:4px;padding:3px 9px;font-size:0.67rem;font-weight:700;">100 CALLS</span>
            <span style="background:#f0fdf4;color:#166534;border-radius:4px;padding:3px 9px;font-size:0.67rem;font-weight:700;">10 COMPANIES</span>
            <span style="background:#fffbeb;color:#92400e;border-radius:4px;padding:3px 9px;font-size:0.67rem;font-weight:700;">5 INDUSTRIES</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("Analyze Sample Dataset →", key="btn_sample"):
            with st.spinner("Loading transcripts…"):
                transcripts = load_sample_transcripts()
            _start_analysis(transcripts, f"Sample dataset · {len(transcripts)} calls")

def _start_analysis(transcripts, source_label):
    st.session_state["_pending_transcripts"] = transcripts
    st.session_state["total_fetched"]        = len(transcripts)
    st.session_state["source_label"]         = source_label
    st.session_state["stage"]                = "loading"
    st.rerun()

# ── LOADING ────────────────────────────────────────────────────
STEP_DESCRIPTIONS = [
    ("Reading the transcript",        "Pulling out what was actually said."),
    ("Understanding the customer",    "Figuring out mood, concerns, and risk."),
    ("Spotting issues & objections",  "Finding what frustrated the customer."),
    ("Classifying the call",          "Tagging call type and resolution status."),
    ("Grading the agent",             "Reviewing how well the call was handled."),
    ("Writing next steps",            "Drafting actions and follow-ups."),
]

def render_loading():
    transcripts = st.session_state.get("_pending_transcripts", [])
    if not transcripts:
        st.session_state["stage"] = "home"
        st.rerun()
        return

    total = len(transcripts)
    with st.sidebar:
        _sidebar_logo()

    _, col, _ = st.columns([1, 5, 1])
    with col:
        st.markdown(f"""
        <div style="padding:4rem 0 0;text-align:center;">
          <div style="font-family:'Lora',serif;font-size:2.1rem;color:#1c1a18;letter-spacing:-0.02em;margin-bottom:0.55rem;">
            Analyzing {total} calls
          </div>
          <div style="font-size:0.88rem;color:#857f78;max-width:420px;margin:0 auto 2.8rem;line-height:1.75;">
            Working through each transcript one by one, extracting insights in 6 steps per call.
          </div>
        </div>
        """, unsafe_allow_html=True)

        overall_label = st.empty()
        overall_bar   = st.progress(0)
        st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
        status_panel  = st.empty()
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)

        steps_html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;">'
        for n, (title, desc) in enumerate(STEP_DESCRIPTIONS, 1):
            steps_html += f"""
            <div style="background:#fff;border:1.5px solid #e4e2dc;border-radius:9px;
              padding:0.85rem 1rem;display:flex;gap:0.75rem;align-items:flex-start;">
              <div style="width:24px;height:24px;border-radius:50%;background:#eef2ff;
                color:#1d4ed8;font-size:0.7rem;font-weight:700;display:flex;
                align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;">{n}</div>
              <div>
                <div style="font-size:0.78rem;font-weight:600;color:#1c1a18;margin-bottom:0.15rem;">{title}</div>
                <div style="font-size:0.72rem;color:#857f78;line-height:1.5;">{desc}</div>
              </div>
            </div>"""
        steps_html += "</div>"
        st.markdown(steps_html, unsafe_allow_html=True)

    def cb(i, total, call_id):
        pct = (i + 1) / total
        overall_bar.progress(pct)
        overall_label.markdown(
            f'<div style="text-align:center;font-size:0.78rem;font-weight:600;color:#857f78;margin-bottom:0.5rem;">'
            f'Call {i+1} of {total} &nbsp;·&nbsp; '
            f'<span style="color:#1c1a18;">{round(pct*100)}% complete</span></div>',
            unsafe_allow_html=True,
        )
        step_idx = i % len(STEP_DESCRIPTIONS)
        step_title, step_desc = STEP_DESCRIPTIONS[step_idx]
        status_panel.markdown(f"""
        <div style="background:#fff;border:1.5px solid #e4e2dc;border-left:4px solid #1d4ed8;
          border-radius:0 10px 10px 0;padding:1rem 1.4rem;display:flex;gap:1rem;align-items:center;">
          <div style="width:36px;height:36px;border-radius:50%;background:#eef2ff;
            color:#1d4ed8;font-size:0.75rem;font-weight:700;display:flex;
            align-items:center;justify-content:center;flex-shrink:0;">{step_idx+1}</div>
          <div>
            <div style="font-size:0.62rem;font-weight:700;color:#857f78;text-transform:uppercase;
              letter-spacing:0.1em;margin-bottom:0.2rem;">Now working on · {call_id}</div>
            <div style="font-size:0.92rem;font-weight:600;color:#1c1a18;">{step_title}</div>
            <div style="font-size:0.78rem;color:#857f78;margin-top:0.15rem;">{step_desc}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    results = analyze_batch(transcripts, cb)
    overall_bar.progress(1.0)
    overall_label.markdown(
        '<div style="text-align:center;font-size:0.82rem;font-weight:600;color:#166534;">'
        '✓ All calls analyzed — building your dashboard…</div>',
        unsafe_allow_html=True,
    )
    status_panel.empty()

    st.session_state["results_df"]           = pd.DataFrame(results)
    st.session_state["stage"]                = "dashboard"
    st.session_state["_pending_transcripts"] = None
    st.rerun()

# ── SIDEBAR FILTERS ────────────────────────────────────────────
def render_sidebar_dashboard(df_all: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        _sidebar_logo()
        st.markdown(
            '<div style="font-size:0.61rem;font-weight:700;color:#302e2c;'
            'text-transform:uppercase;letter-spacing:0.14em;padding:0 1.2rem;margin-bottom:0.75rem;">Filter Calls</div>',
            unsafe_allow_html=True,
        )

        sentiments  = _safe_list(df_all, "sentiment")
        resolutions = _safe_list(df_all, "resolution_status")
        call_types  = _safe_list(df_all, "call_type")
        companies   = _safe_list(df_all, "company")
        outcomes    = _safe_list(df_all, "outcome")

        sel_sent = st.multiselect("Sentiment",   sentiments,  default=sentiments,  key="f_sent")
        sel_res  = st.multiselect("Resolution",  resolutions, default=resolutions, key="f_res")
        sel_ct   = st.multiselect("Call Type",   call_types,  default=call_types,  key="f_ct")
        sel_co   = st.multiselect("Company",     companies,   default=companies,   key="f_co")
        sel_out  = st.multiselect("Outcome",     outcomes,    default=outcomes,    key="f_out")

        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
        if st.button("Reset Filters", key="reset"):
            for k in ["f_sent","f_res","f_ct","f_co","f_out"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown('<hr style="border-color:#232220;margin:1.1rem 0;">', unsafe_allow_html=True)
        if st.button("← New Analysis", key="new_analysis"):
            for k in list(DEFAULTS.keys()) + ["f_sent","f_res","f_ct","f_co","f_out"]:
                st.session_state.pop(k, None)
            st.cache_data.clear()
            st.rerun()

        st.markdown(f"""
        <div style="padding:0.7rem 1.2rem;font-size:0.69rem;color:#302e2c;line-height:1.9;">
          {st.session_state.source_label}<br>
          <span style="color:#232220;">Groq · LLaMA 3.3 70B</span>
        </div>
        """, unsafe_allow_html=True)

    df = df_all.copy()
    if sel_sent: df = df[df["sentiment"].isin(sel_sent)]
    if sel_res:  df = df[df["resolution_status"].isin(sel_res)]
    if sel_ct:   df = df[df["call_type"].isin(sel_ct)]
    if sel_co:   df = df[df["company"].isin(sel_co)]
    if sel_out:  df = df[df["outcome"].isin(sel_out)]
    return df

# ── DASHBOARD ──────────────────────────────────────────────────
def render_dashboard():
    df_all        = st.session_state["results_df"]
    total_fetched = st.session_state["total_fetched"]
    df            = render_sidebar_dashboard(df_all)

    n    = len(df)
    note = (f" · Filtered to {n} of {len(df_all)}"
            if n < len(df_all)
            else (f" · Showing {len(df_all)} of {total_fetched}"
                  if len(df_all) < total_fetched else ""))

    st.markdown(f"""
    <div style="padding:1.8rem 0 1.8rem;border-bottom:1.5px solid #e4e2dc;margin-bottom:2rem;">
      <div style="font-family:'Lora',serif;font-size:1.9rem;color:#1c1a18;letter-spacing:-0.02em;line-height:1;">
        Close<span style="color:#1d4ed8;">Call</span>
        <span style="font-family:'Inter',sans-serif;font-size:0.72rem;font-weight:500;
          color:#857f78;margin-left:0.9rem;">Dashboard</span>
      </div>
      <div style="font-size:0.74rem;color:#857f78;margin-top:0.3rem;">
        {st.session_state['source_label']}{note}
      </div>
    </div>
    """, unsafe_allow_html=True)

    render_kpis(df, total_fetched)
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    render_charts(df)
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    render_table_section(df)

# ── KPIs — FIX 2: no CSAT, replaced with Avg Rep Score ────────
def render_kpis(df: pd.DataFrame, total_fetched: int):
    n   = len(df)
    pos = len(df[df["sentiment"] == "Positive"])
    neg = len(df[df["sentiment"] == "Negative"])
    mix = len(df[df["sentiment"] == "Mixed"])

    # FIX: count both Negative AND Mixed as unfavorable for the % display
    neg_total   = neg + mix
    pos_pct     = round(pos / n * 100) if n else 0
    neg_pct     = round(neg_total / n * 100) if n else 0
    note        = f"of {total_fetched}" if n < total_fetched else "calls"

    # Avg rep score (from AI analysis — always present)
    rep_scores = pd.to_numeric(df.get("rep_score", pd.Series(dtype=float)), errors="coerce").dropna()
    avg_rep    = f"{rep_scores.mean():.1f}/5" if len(rep_scores) else "—"

    # Escalated count
    escalated = len(df[df["resolution_status"] == "Escalated"]) if "resolution_status" in df.columns else 0

    cols = st.columns(5)
    cards = [
        ("#1d4ed8", "Calls Analyzed",     str(n),         note),
        ("#166534", "Positive Sentiment", f"{pos_pct}%",  f"{pos} calls"),
        ("#991b1b", "Negative / Mixed",   f"{neg_pct}%",  f"{neg_total} calls"),
        ("#b45309", "Avg Agent Score",    avg_rep,        "AI-graded performance"),
        ("#7c3aed", "Escalated",          str(escalated), "needs attention"),
    ]
    for col, (accent, label, big, sub) in zip(cols, cards):
        with col:
            st.markdown(f"""
            <div style="background:#fff;border:1.5px solid #e4e2dc;border-top:3px solid {accent};
              border-radius:10px;padding:1.1rem 1.2rem;">
              <div style="font-size:0.58rem;font-weight:700;color:#857f78;text-transform:uppercase;
                letter-spacing:0.11em;margin-bottom:0.4rem;">{label}</div>
              <div style="font-size:2rem;font-weight:800;color:#1c1a18;line-height:1;
                letter-spacing:-0.04em;">{big}</div>
              <div style="font-size:0.67rem;color:#857f78;margin-top:0.35rem;">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

# ── CHARTS — FIX 3: no duplicate kwargs ───────────────────────
def render_charts(df: pd.DataFrame):
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
        <div style="background:#fff;border:1.5px solid #e4e2dc;border-radius:10px;padding:1.3rem 1.5rem 0;">
          <div style="font-size:0.83rem;font-weight:700;color:#1c1a18;">Sentiment Breakdown</div>
          <div style="font-size:0.71rem;color:#857f78;margin-bottom:0.5rem;">How customers felt across all calls</div>
        </div>
        """, unsafe_allow_html=True)
        sent = df["sentiment"].value_counts().reset_index()
        sent.columns = ["Sentiment", "Count"]
        cmap = {"Positive":"#166534","Negative":"#991b1b","Mixed":"#b45309","Neutral":"#6b7280"}
        fig = px.bar(sent, x="Sentiment", y="Count", color="Sentiment",
                     color_discrete_map=cmap, text="Count")
        fig.update_traces(textposition="outside", marker_line_width=0, textfont_size=12)
        # Pass xaxis + yaxis directly — NOT via **_chart_base() to avoid collision
        fig.update_layout(
            showlegend=False,
            xaxis=dict(gridcolor="#f0ede8", zerolinecolor="#f0ede8", title=None),
            yaxis=dict(gridcolor="#f0ede8", zerolinecolor="#f0ede8", title=None),
            **_chart_base(),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        if "call_type" in df.columns and df["call_type"].nunique() > 0:
            st.markdown("""
            <div style="background:#fff;border:1.5px solid #e4e2dc;border-radius:10px;padding:1.3rem 1.5rem 0;">
              <div style="font-size:0.83rem;font-weight:700;color:#1c1a18;">Call Type Breakdown</div>
              <div style="font-size:0.71rem;color:#857f78;margin-bottom:0.5rem;">What customers are calling about</div>
            </div>
            """, unsafe_allow_html=True)
            ct = df["call_type"].value_counts().reset_index()
            ct.columns = ["Call Type", "Count"]
            fig2 = px.bar(ct, x="Count", y="Call Type", orientation="h",
                          color="Count", color_continuous_scale=["#bfdbfe","#1d4ed8"],
                          text="Count")
            fig2.update_traces(textposition="outside", marker_line_width=0, textfont_size=11)
            # KEY FIX: pass yaxis with autorange reversed directly — no **_chart_base() overlap
            fig2.update_layout(
                showlegend=False,
                coloraxis_showscale=False,
                xaxis=dict(gridcolor="#f0ede8", zerolinecolor="#f0ede8", title=None),
                yaxis=dict(gridcolor="#f0ede8", zerolinecolor="#f0ede8", title=None, autorange="reversed"),
                **_chart_base(),
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Call type data not available.")

# ── TABLE ──────────────────────────────────────────────────────
def render_table_section(df: pd.DataFrame):
    st.markdown('<div style="font-size:0.83rem;font-weight:700;color:#1c1a18;margin-bottom:0.7rem;">All Calls</div>',
                unsafe_allow_html=True)

    s_col, _ = st.columns([5, 4])
    with s_col:
        search = st.text_input("", placeholder="🔍  Search by company, issue, objection…",
                               label_visibility="collapsed", key="search")

    fdf = df.copy()
    if search:
        mask = pd.Series(False, index=fdf.index)
        for col in ["id","company","call_type","key_issue","top_objection","customer_name"]:
            if col in fdf.columns:
                mask |= fdf[col].astype(str).str.contains(search, case=False, na=False)
        fdf = fdf[mask]

    st.markdown(f'<div style="font-size:0.71rem;color:#857f78;margin-bottom:0.6rem;">{len(fdf)} of {len(df)} calls</div>',
                unsafe_allow_html=True)

    if fdf.empty:
        st.info("No calls match your search.")
        return

    rows_html = ""
    for _, r in fdf.head(60).iterrows():
        key_issue = _v(r, "key_issue")
        next_step = _v(r, "next_step")
        rows_html += f"""
        <tr style="border-bottom:1px solid #f6f5f2;">
          <td style="padding:10px 12px;font-weight:600;color:#1c1a18;white-space:nowrap;font-size:0.78rem;">{_v(r,'id')}</td>
          <td style="padding:10px 12px;color:#4a4642;font-size:0.8rem;">{_v(r,'company')}</td>
          <td style="padding:10px 12px;">{sent_pill(_v(r,'sentiment','Neutral'))}</td>
          <td style="padding:10px 12px;">{res_pill(_v(r,'resolution_status','—'))}</td>
          <td style="padding:10px 12px;color:#4a4642;font-size:0.78rem;max-width:220px;line-height:1.5;">{key_issue}</td>
          <td style="padding:10px 12px;color:#4a4642;font-size:0.78rem;max-width:220px;line-height:1.5;">{next_step}</td>
        </tr>"""

    headers = ["Call ID", "Company", "Sentiment", "Resolution", "Key Issue", "Next Step"]
    th = "".join(f'<th style="padding:9px 12px;text-align:left;font-size:0.6rem;font-weight:700;color:#857f78;text-transform:uppercase;letter-spacing:0.1em;white-space:nowrap;">{h}</th>' for h in headers)

    st.markdown(f"""
    <div style="background:#fff;border:1.5px solid #e4e2dc;border-radius:10px;overflow:hidden;margin-bottom:1.5rem;">
      <table style="width:100%;border-collapse:collapse;font-size:0.81rem;">
        <thead><tr style="background:#faf9f7;border-bottom:1.5px solid #e4e2dc;">{th}</tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

    if len(fdf) > 60:
        st.caption(f"Showing first 60 of {len(fdf)} results.")

    render_detail(fdf)

# ── CALL DETAIL ────────────────────────────────────────────────
def render_detail(df: pd.DataFrame):
    st.markdown("""
    <div style="height:0.4rem;"></div>
    <div style="font-size:0.83rem;font-weight:700;color:#1c1a18;margin-bottom:0.15rem;">Call Detail</div>
    <div style="font-size:0.71rem;color:#857f78;margin-bottom:0.75rem;">
      Select a call to see the full transcript, AI analysis, recommended actions, and generate a follow-up email.
    </div>
    """, unsafe_allow_html=True)

    sel = st.selectbox("", df["id"].tolist(), label_visibility="collapsed", key="detail_sel")
    r   = df[df["id"] == sel].iloc[0]

    # Meta chips
    st.markdown(f"""
    <div style="display:flex;flex-wrap:wrap;gap:0.55rem;margin-bottom:1.1rem;">
      {_meta_chip("🏢 Company",   _v(r,'company'))}
      {_meta_chip("📞 Call Type", _v(r,'call_type'))}
      {_meta_chip("📋 Outcome",   _v(r,'outcome'))}
    </div>
    """, unsafe_allow_html=True)

    sfg, sbg = SENT_COLORS.get(_v(r,"sentiment"), ("#4b5563","#f3f4f6"))
    rfg, rbg = RESOLUTION_COLORS.get(_v(r,"resolution_status"), ("#4b5563","#f3f4f6"))

    def chip(lbl_text, val, fg, bg):
        return f"""<div style="background:{bg};border-radius:8px;padding:0.85rem 1.1rem;">
          <div style="font-size:0.61rem;font-weight:700;color:{fg}90;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.2rem;">{lbl_text}</div>
          <div style="font-size:0.87rem;font-weight:700;color:{fg};">{val}</div>
        </div>"""

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(chip("Sentiment",   _v(r,"sentiment"),        sfg, sbg), unsafe_allow_html=True)
    with c2: st.markdown(chip("Resolution",  _v(r,"resolution_status"), rfg, rbg), unsafe_allow_html=True)
    with c3: st.markdown(chip("Agent Score", f"{_v(r,'rep_score')}/5", "#1c1a18","#faf9f7"), unsafe_allow_html=True)
    with c4: st.markdown(chip("Lead Type",   _v(r,"lead_type"),         "#1c1a18","#faf9f7"), unsafe_allow_html=True)

    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["📄 Transcript", "🧠 AI Insights", "✅ Actions", "✉️ Follow-up Email"])

    with t1:
        content = str(r.get("content","No transcript available."))
        display = (content
            .replace("Agent:",    "<strong style='color:#1d4ed8;'>🎙 Agent:</strong>")
            .replace("Customer:", "<strong style='color:#166534;'>👤 Customer:</strong>")
            .replace("**Sales Rep**", "<strong style='color:#1d4ed8;'>🎙 Sales Rep:</strong>")
            .replace("**Customer**",  "<strong style='color:#166534;'>👤 Customer:</strong>")
            .replace("\n","<br>"))
        st.markdown(f"""
        <div style="background:#faf9f7;border:1.5px solid #e4e2dc;border-radius:10px;
          padding:1.3rem 1.7rem;font-size:0.82rem;color:#4a4642;line-height:2.1;
          max-height:400px;overflow-y:auto;">{display}</div>
        """, unsafe_allow_html=True)

    with t2:
        ia, ib = st.columns(2)
        def dp(label, val):
            return f"""<div style="background:#fff;border:1.5px solid #e4e2dc;border-radius:9px;
              padding:1rem 1.2rem;margin-bottom:0.65rem;">
              <div style="font-size:0.61rem;font-weight:700;color:#857f78;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.28rem;">{label}</div>
              <div style="font-size:0.84rem;color:#1c1a18;line-height:1.65;">{val}</div>
            </div>"""
        with ia:
            st.markdown(dp("Summary",        _v(r,"summary")),       unsafe_allow_html=True)
            st.markdown(dp("Sentiment Arc",  _v(r,"sentiment_arc")), unsafe_allow_html=True)
            st.markdown(dp("Key Issue",      _v(r,"key_issue")),     unsafe_allow_html=True)
        with ib:
            st.markdown(dp("Top Objection",  _v(r,"top_objection")), unsafe_allow_html=True)
            st.markdown(dp("Call Outcome",   _v(r,"outcome")),       unsafe_allow_html=True)
            try: rep = int(r.get("rep_score",0))
            except: rep = 0
            st.markdown(f"""
            <div style="background:#fff;border:1.5px solid #e4e2dc;border-radius:9px;padding:1rem 1.2rem;margin-bottom:0.65rem;">
              <div style="font-size:0.61rem;font-weight:700;color:#857f78;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Agent Score</div>
              <div style="margin-bottom:0.3rem;">{score_dots(rep)}</div>
              <div style="font-size:0.84rem;color:#1c1a18;line-height:1.65;">{_v(r,'rep_score_reason')}</div>
            </div>
            """, unsafe_allow_html=True)
        q = _v(r,"standout_quote")
        if q and q != "—":
            st.markdown(f"""
            <div style="border-left:3px solid #1d4ed8;padding:0.75rem 1.1rem;background:#eef2ff;
              border-radius:0 8px 8px 0;font-style:italic;color:#4a4642;font-size:0.84rem;margin-top:0.3rem;">
              "{q}"</div>
            """, unsafe_allow_html=True)

    with t3:
        ns = _v(r,"next_step")
        if ns and ns != "—":
            st.markdown(f"""
            <div style="background:#eef2ff;border:1.5px solid #bfdbfe;border-left:4px solid #1d4ed8;
              border-radius:0 10px 10px 0;padding:0.95rem 1.3rem;margin-bottom:1rem;">
              <div style="font-size:0.61rem;font-weight:700;color:#1d4ed8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.25rem;">Immediate Next Step</div>
              <div style="font-size:0.9rem;font-weight:600;color:#1e3a8a;line-height:1.6;">{ns}</div>
            </div>
            """, unsafe_allow_html=True)

        actions = r.get("recommended_actions",[])
        if isinstance(actions, str):
            try: actions = json.loads(actions)
            except: actions = [actions]
        if actions:
            items_html = "".join(f"""
            <div style="display:flex;gap:0.7rem;align-items:flex-start;padding:0.75rem 0;
              border-bottom:1px solid #f6f5f2;font-size:0.83rem;color:#1c1a18;line-height:1.55;">
              <div style="min-width:22px;height:22px;background:#eef2ff;color:#1d4ed8;font-weight:700;
                font-size:0.69rem;border-radius:50%;display:flex;align-items:center;justify-content:center;
                flex-shrink:0;margin-top:1px;">{i}</div>
              <div>{a}</div>
            </div>""" for i, a in enumerate(actions, 1))
            st.markdown(f"""
            <div style="background:#fff;border:1.5px solid #e4e2dc;border-radius:10px;padding:0.3rem 1.2rem 0.3rem;">
              <div style="font-size:0.61rem;font-weight:700;color:#857f78;text-transform:uppercase;
                letter-spacing:0.1em;padding-top:0.7rem;margin-bottom:0.1rem;">Recommended Actions</div>
              {items_html}
            </div>
            """, unsafe_allow_html=True)

    with t4:
        ek = f"email_{sel}"
        if ek not in st.session_state:
            st.session_state[ek] = None

        if st.session_state[ek] is None:
            st.markdown("""
            <div style="font-size:0.82rem;color:#857f78;margin-bottom:1.2rem;line-height:1.75;">
              Generate a ready-to-send follow-up email addressed to the customer by name —
              referencing their issue, resolution status, order/reference, and agreed next steps.
            </div>
            """, unsafe_allow_html=True)
            _, bc, _ = st.columns([2,3,2])
            with bc:
                if st.button("Generate Follow-up Email", key=f"gen_{sel}"):
                    with st.spinner("Writing email…"):
                        email = generate_email(
                            customer_name    = _v(r,"customer_name"),
                            summary          = _v(r,"summary"),
                            key_issue        = _v(r,"key_issue"),
                            resolution_status= _v(r,"resolution_status"),
                            next_step        = _v(r,"next_step"),
                            order_or_ref     = _v(r,"id"),
                            sentiment        = _v(r,"sentiment"),
                            call_type        = _v(r,"call_type"),
                        )
                    st.session_state[ek] = email
                    st.rerun()
        else:
            st.markdown(f"""
            <div style="background:#faf9f7;border:1.5px solid #e4e2dc;border-radius:10px;
              padding:1.3rem 1.7rem;font-size:0.86rem;color:#1c1a18;line-height:1.9;white-space:pre-wrap;">
              {st.session_state[ek]}</div>
            """, unsafe_allow_html=True)
            ca, cb_col, _ = st.columns([3,2,4])
            with ca:
                st.code(st.session_state[ek], language=None)
            with cb_col:
                if st.button("Regenerate", key=f"regen_{sel}"):
                    st.session_state[ek] = None
                    st.rerun()

# ── ROUTER ─────────────────────────────────────────────────────
stage = st.session_state["stage"]
if   stage == "home":      render_home()
elif stage == "loading":   render_loading()
elif stage == "dashboard": render_dashboard()
else:
    st.session_state["stage"] = "home"
    st.rerun()

transcripts = load_sample_transcripts()
