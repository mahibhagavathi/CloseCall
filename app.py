import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_sample_transcripts, load_csv_transcripts
from analyzer import analyze_batch, generate_email

# ──────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CloseCall · AI Call Agent",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap');

:root {
  --bg:        #f5f4f0;
  --surface:   #ffffff;
  --border:    #e8e6e0;
  --text:      #1a1917;
  --muted:     #8a8680;
  --accent:    #1c4ed8;
  --accent-lt: #eff3ff;
  --green:     #166534;
  --green-lt:  #f0fdf4;
  --red:       #991b1b;
  --red-lt:    #fef2f2;
  --amber:     #92400e;
  --amber-lt:  #fffbeb;
}

*, html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}
.stApp { background: var(--bg) !important; }

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"]    { display: none; }
[data-testid="stDecoration"] { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #111110 !important;
    border-right: 1px solid #2a2927 !important;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }
section[data-testid="stSidebar"] * { color: #9a9691 !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #1c1b1a !important;
    border-color: #2a2927 !important;
    color: #e8e6e0 !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background: #1c4ed8 !important;
}
[data-testid="stSidebar"] span { color: #e8e6e0 !important; }

/* ── Buttons ── */
.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.65rem 1.6rem !important;
    width: 100% !important;
    letter-spacing: 0.01em !important;
    transition: background 0.15s, box-shadow 0.15s !important;
}
.stButton > button:hover {
    background: #1d4ed8 !important;
    box-shadow: 0 4px 16px rgba(28,78,216,0.25) !important;
}

/* ── Progress ── */
.stProgress > div > div { background: var(--accent) !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1.5px solid var(--border) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    color: var(--muted) !important;
    padding: 0.55rem 1.1rem !important;
    border-radius: 0 !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -1.5px !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] section {
    background: var(--surface) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: var(--accent) !important;
}

/* ── Text input ── */
div[data-testid="stTextInput"] input {
    border-radius: 6px !important;
    border: 1.5px solid var(--border) !important;
    font-size: 0.875rem !important;
    background: var(--surface) !important;
    padding: 0.5rem 0.85rem !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(28,78,216,0.08) !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* ── Selectbox ── */
div[data-baseweb="select"] > div {
    border-radius: 6px !important;
    border: 1.5px solid var(--border) !important;
    background: var(--surface) !important;
    font-size: 0.875rem !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────
# DESIGN HELPERS
# ──────────────────────────────────────────────────────────────
SENT_COLORS = {
    "Positive": ("#166534", "#f0fdf4"),
    "Negative": ("#991b1b", "#fef2f2"),
    "Mixed":    ("#92400e", "#fffbeb"),
    "Neutral":  ("#4b5563", "#f3f4f6"),
}
LEAD_COLORS = {
    "Hot":  ("#991b1b", "#fef2f2"),
    "Warm": ("#92400e", "#fffbeb"),
    "Cold": ("#1e40af", "#eff3ff"),
}

def pill(text, fg, bg):
    return (f'<span style="display:inline-block;background:{bg};color:{fg};'
            f'border-radius:4px;padding:2px 9px;font-size:0.69rem;font-weight:700;'
            f'letter-spacing:0.06em;text-transform:uppercase;">{text}</span>')

def sent_pill(v):
    fg, bg = SENT_COLORS.get(v, ("#4b5563", "#f3f4f6"))
    return pill(v, fg, bg)

def lead_pill(v):
    fg, bg = LEAD_COLORS.get(v, ("#1e40af", "#eff3ff"))
    return pill(v, fg, bg)

def score_dots(n):
    try: n = int(n)
    except: n = 0
    html = ""
    for i in range(1, 6):
        c = "#1c4ed8" if i <= n else "#e8e6e0"
        html += f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{c};margin-right:3px;"></span>'
    return html

# ──────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────
def render_sidebar_dashboard(df_all):
    with st.sidebar:
        st.markdown("""
        <div style="padding:1.8rem 1.2rem 1.2rem;border-bottom:1px solid #2a2927;margin-bottom:1.5rem;">
          <div style="font-family:'DM Serif Display',serif;font-size:1.7rem;color:#f5f4f0;letter-spacing:-0.02em;line-height:1.1;">
            Close<span style="color:#4f83f7;">Call</span>
          </div>
          <div style="font-size:0.65rem;font-weight:600;color:#3a3835;text-transform:uppercase;letter-spacing:0.16em;margin-top:0.35rem;">
            Customer Support Intelligence
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:0.63rem;font-weight:700;color:#3a3835;text-transform:uppercase;letter-spacing:0.14em;padding:0 1.2rem;margin-bottom:0.75rem;">Filter Calls</div>', unsafe_allow_html=True)

        companies  = sorted(df_all["company"].dropna().unique().tolist())
        sentiments = sorted(df_all["sentiment"].dropna().unique().tolist())
        leads      = sorted(df_all["lead_type"].dropna().unique().tolist())
        outcomes   = sorted(df_all["outcome"].dropna().unique().tolist())

        sel_co   = st.multiselect("Company",   companies,  default=companies,  key="f_co")
        sel_sent = st.multiselect("Sentiment", sentiments, default=sentiments, key="f_sent")
        sel_lead = st.multiselect("Lead Type", leads,      default=leads,      key="f_lead")
        sel_out  = st.multiselect("Outcome",   outcomes,   default=outcomes,   key="f_out")

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
        if st.button("Reset Filters", key="reset"):
            for k in ["f_co","f_sent","f_lead","f_out"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown('<hr style="border-color:#2a2927;margin:1.2rem 0;">', unsafe_allow_html=True)
        if st.button("← New Analysis", key="new_analysis"):
            for k in list(DEFAULTS.keys()) + ["f_co","f_sent","f_lead","f_out"]:
                st.session_state.pop(k, None)
            st.cache_data.clear()
            st.rerun()

        st.markdown(f"""
        <div style="padding:0.8rem 1.2rem;font-size:0.7rem;color:#3a3835;line-height:1.8;">
          {st.session_state.source_label}<br>
          <span style="color:#2a2927;">Powered by Groq · LLaMA 3.3 70B</span>
        </div>
        """, unsafe_allow_html=True)

    df = df_all.copy()
    if sel_co:   df = df[df["company"].isin(sel_co)]
    if sel_sent: df = df[df["sentiment"].isin(sel_sent)]
    if sel_lead: df = df[df["lead_type"].isin(sel_lead)]
    if sel_out:  df = df[df["outcome"].isin(sel_out)]
    return df

# ──────────────────────────────────────────────────────────────
# HOME
# ──────────────────────────────────────────────────────────────
def render_home():
    with st.sidebar:
        st.markdown("""
        <div style="padding:1.8rem 1.2rem 1.2rem;border-bottom:1px solid #2a2927;margin-bottom:1.5rem;">
          <div style="font-family:'DM Serif Display',serif;font-size:1.7rem;color:#f5f4f0;letter-spacing:-0.02em;">
            Close<span style="color:#4f83f7;">Call</span>
          </div>
          <div style="font-size:0.65rem;font-weight:600;color:#3a3835;text-transform:uppercase;letter-spacing:0.16em;margin-top:0.35rem;">
            Customer Support Intelligence
          </div>
        </div>
        <div style="padding:0 1.2rem;font-size:0.78rem;color:#5a5854;line-height:2.1;">
          <div>🎧&nbsp; Customer support call analysis</div>
          <div>💬&nbsp; Objection &amp; issue detection</div>
          <div>📊&nbsp; Sentiment &amp; tone tracking</div>
          <div>🔥&nbsp; Lead scoring (Hot / Warm / Cold)</div>
          <div>⭐&nbsp; Agent performance scoring</div>
          <div>✉️&nbsp; AI follow-up email writer</div>
          <div>📋&nbsp; Recommended next actions</div>
        </div>
        """, unsafe_allow_html=True)

    # Hero section
    st.markdown("""
    <div style="padding:3.5rem 0 3rem 0;">
      <div style="display:inline-block;background:#eff3ff;color:#1c4ed8;font-size:0.7rem;
        font-weight:700;text-transform:uppercase;letter-spacing:0.14em;padding:4px 12px;
        border-radius:4px;margin-bottom:1.2rem;">AI Agent for Support Teams</div>
      <div style="font-family:'DM Serif Display',serif;font-size:3.2rem;color:#1a1917;
        letter-spacing:-0.03em;line-height:1.1;margin-bottom:1.1rem;">
        Every call, fully<br><em style="color:#1c4ed8;">understood.</em>
      </div>
      <div style="font-size:1rem;color:#6b6860;max-width:480px;line-height:1.75;">
        CloseCall is an AI agent that reads your customer support transcripts 
        and surfaces what matters — sentiment, objections, lead quality, 
        agent scores, and ready-to-send follow-up emails.
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_a, gap, col_b = st.columns([11, 1, 11])

    with col_a:
        st.markdown("""
        <div style="background:#fff;border:1.5px solid #e8e6e0;border-radius:12px;
          padding:2rem 2rem 1.5rem;margin-bottom:1rem;">
          <div style="font-size:0.75rem;font-weight:700;color:#8a8680;text-transform:uppercase;
            letter-spacing:0.12em;margin-bottom:0.5rem;">Option A</div>
          <div style="font-size:1.05rem;font-weight:700;color:#1a1917;margin-bottom:0.5rem;">
            Upload Your Transcripts
          </div>
          <div style="font-size:0.83rem;color:#6b6860;line-height:1.7;margin-bottom:1.4rem;">
            Drop a <code style="background:#f5f4f0;padding:1px 6px;border-radius:3px;font-size:0.8rem;">CSV</code> file 
            with a <code style="background:#f5f4f0;padding:1px 6px;border-radius:3px;font-size:0.8rem;">transcript</code> or 
            <code style="background:#f5f4f0;padding:1px 6px;border-radius:3px;font-size:0.8rem;">content</code> column.<br>
            Optional: <code style="background:#f5f4f0;padding:1px 6px;border-radius:3px;font-size:0.8rem;">id</code> and 
            <code style="background:#f5f4f0;padding:1px 6px;border-radius:3px;font-size:0.8rem;">company</code> columns.
          </div>
        </div>
        """, unsafe_allow_html=True)
        uploaded = st.file_uploader("", type=["csv"], label_visibility="collapsed", key="csv_upload")
        if uploaded:
            if st.button("Analyze Uploaded Calls →", key="btn_upload"):
                try:
                    transcripts = load_csv_transcripts(uploaded)
                    _start_analysis(transcripts, f"{len(transcripts)} uploaded calls")
                except Exception as e:
                    st.error(f"CSV error: {e}")

    with gap:
        st.markdown("""
        <div style="display:flex;align-items:center;justify-content:center;height:260px;">
          <div style="position:relative;width:1px;height:120px;background:#e8e6e0;">
            <span style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
              background:#f5f4f0;color:#c4c2bc;font-size:0.7rem;font-weight:600;
              padding:5px 0;white-space:nowrap;">or</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div style="background:#fff;border:1.5px solid #e8e6e0;border-radius:12px;
          padding:2rem 2rem 1.5rem;margin-bottom:1rem;">
          <div style="font-size:0.75rem;font-weight:700;color:#8a8680;text-transform:uppercase;
            letter-spacing:0.12em;margin-bottom:0.5rem;">Option B</div>
          <div style="font-size:1.05rem;font-weight:700;color:#1a1917;margin-bottom:0.5rem;">
            Try the Sample Dataset
          </div>
          <div style="font-size:0.83rem;color:#6b6860;line-height:1.7;margin-bottom:1.4rem;">
            100 real support call transcripts across fashion, real estate,
            finance, healthcare &amp; tech. No upload needed — start in seconds.
          </div>
          <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.2rem;">
            <span style="background:#eff3ff;color:#1c4ed8;border-radius:4px;padding:3px 10px;
              font-size:0.69rem;font-weight:700;letter-spacing:0.05em;">100 CALLS</span>
            <span style="background:#f0fdf4;color:#166534;border-radius:4px;padding:3px 10px;
              font-size:0.69rem;font-weight:700;letter-spacing:0.05em;">10 COMPANIES</span>
            <span style="background:#fffbeb;color:#92400e;border-radius:4px;padding:3px 10px;
              font-size:0.69rem;font-weight:700;letter-spacing:0.05em;">5 INDUSTRIES</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Analyze Sample Dataset →", key="btn_sample"):
            with st.spinner("Loading transcripts..."):
                transcripts = load_sample_transcripts()
            _start_analysis(transcripts, f"Sample dataset · {len(transcripts)} calls")


def _start_analysis(transcripts, label):
    st.session_state["_pending_transcripts"] = transcripts
    st.session_state["total_fetched"] = len(transcripts)
    st.session_state["source_label"] = label
    st.session_state["stage"] = "loading"
    st.rerun()

# ──────────────────────────────────────────────────────────────
# LOADING  ← BUG FIX: pass progress bar object into callback
# ──────────────────────────────────────────────────────────────
def render_loading():
    transcripts = st.session_state.get("_pending_transcripts", [])
    if not transcripts:
        st.session_state["stage"] = "home"
        st.rerun()
        return

    total = len(transcripts)

    _, col, _ = st.columns([1, 4, 1])
    with col:
        st.markdown(f"""
        <div style="padding:5rem 0 2.5rem;text-align:center;">
          <div style="font-family:'DM Serif Display',serif;font-size:2.2rem;color:#1a1917;
            margin-bottom:0.6rem;">Analyzing {total} calls</div>
          <div style="font-size:0.9rem;color:#8a8680;margin-bottom:3rem;">
            CloseCall's AI agent is reading each transcript and extracting structured insights
          </div>
        </div>
        """, unsafe_allow_html=True)

        steps = ["Fetching transcripts", "AI analysis", "Building dashboard"]
        step_html = '<div style="display:flex;justify-content:center;align-items:center;gap:0;margin-bottom:2.5rem;">'
        for i, s in enumerate(steps):
            done   = i < 1
            active = i == 1
            bg     = "#1c4ed8" if (done or active) else "#e8e6e0"
            tc     = "#1a1917" if (done or active) else "#c4c2bc"
            lc     = "#1c4ed8" if done else "#e8e6e0"
            inner  = "✓" if done else str(i + 1)
            step_html += f"""
            <div style="display:flex;align-items:center;">
              <div style="text-align:center;min-width:110px;">
                <div style="width:34px;height:34px;border-radius:50%;background:{bg};
                  color:#fff;font-size:0.78rem;font-weight:700;display:flex;
                  align-items:center;justify-content:center;margin:0 auto 0.45rem;">{inner}</div>
                <div style="font-size:0.71rem;font-weight:600;color:{tc};">{s}</div>
              </div>
              {"" if i == len(steps)-1 else f'<div style="width:50px;height:2px;background:{lc};margin:0 0.3rem 1.3rem;flex-shrink:0;"></div>'}
            </div>"""
        step_html += "</div>"
        st.markdown(step_html, unsafe_allow_html=True)

        progress_bar = st.progress(0, text="Starting…")

    # ✅ FIX: define callback that wraps the progress bar object
    def cb(i, total, label):
        pct = (i + 1) / total
        progress_bar.progress(pct, text=f"Analyzing call {i+1} of {total} — {label}")

    results = analyze_batch(transcripts, cb)
    progress_bar.empty()

    st.session_state["results_df"] = pd.DataFrame(results)
    st.session_state["stage"] = "dashboard"
    st.session_state["_pending_transcripts"] = None
    st.rerun()

# ──────────────────────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────────────────────
def render_dashboard():
    df_all        = st.session_state["results_df"]
    total_fetched = st.session_state["total_fetched"]
    df            = render_sidebar_dashboard(df_all)

    n_shown = len(df)
    note = ""
    if n_shown < len(df_all):
        note = f" · Filtered: {n_shown} of {len(df_all)}"
    elif len(df_all) < total_fetched:
        note = f" · Showing {len(df_all)} of {total_fetched}"

    st.markdown(f"""
    <div style="padding:1.8rem 0 2rem;border-bottom:1.5px solid #e8e6e0;margin-bottom:2rem;">
      <div style="font-family:'DM Serif Display',serif;font-size:2rem;color:#1a1917;
        letter-spacing:-0.02em;line-height:1;">
        Close<span style="color:#1c4ed8;">Call</span>
        <span style="font-family:'DM Sans',sans-serif;font-size:0.75rem;font-weight:500;
          color:#8a8680;margin-left:1rem;letter-spacing:0;">Dashboard</span>
      </div>
      <div style="font-size:0.76rem;color:#8a8680;margin-top:0.35rem;font-weight:500;">
        {st.session_state['source_label']}{note}
      </div>
    </div>
    """, unsafe_allow_html=True)

    render_kpis(df, total_fetched)
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    render_charts(df)
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    render_table_section(df)

# ──────────────────────────────────────────────────────────────
# KPIs
# ──────────────────────────────────────────────────────────────
def render_kpis(df, total_fetched):
    n       = len(df)
    pos     = len(df[df["sentiment"] == "Positive"])
    neg     = len(df[df["sentiment"] == "Negative"])
    hot     = len(df[df["lead_type"] == "Hot"])
    pos_pct = round(pos / n * 100) if n else 0
    neg_pct = round(neg / n * 100) if n else 0

    note = f"of {total_fetched} total" if n < total_fetched else "calls analyzed"

    k1, k2, k3, k4 = st.columns(4)
    for col, accent, label, big, sub in [
        (k1, "#1c4ed8", "Calls Analyzed",     str(n),         note),
        (k2, "#166534", "Positive Sentiment", f"{pos_pct}%",  f"{pos} calls"),
        (k3, "#991b1b", "Negative Sentiment", f"{neg_pct}%",  f"{neg} calls"),
        (k4, "#b45309", "Hot Leads",          str(hot),       "high intent"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:#fff;border:1.5px solid #e8e6e0;border-top:3px solid {accent};
              border-radius:10px;padding:1.4rem 1.6rem;">
              <div style="font-size:0.63rem;font-weight:700;color:#8a8680;text-transform:uppercase;
                letter-spacing:0.12em;margin-bottom:0.5rem;">{label}</div>
              <div style="font-size:2.4rem;font-weight:800;color:#1a1917;line-height:1;
                letter-spacing:-0.04em;">{big}</div>
              <div style="font-size:0.71rem;color:#8a8680;margin-top:0.4rem;">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# CHARTS
# ──────────────────────────────────────────────────────────────
def _chart_base():
    return dict(
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        font=dict(family="DM Sans, sans-serif", color="#6b6860", size=11),
        margin=dict(l=8, r=8, t=36, b=8),
        xaxis=dict(gridcolor="#f5f4f0", zerolinecolor="#f5f4f0", title=None),
        yaxis=dict(gridcolor="#f5f4f0", zerolinecolor="#f5f4f0", title=None),
    )

def render_charts(df):
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
        <div style="background:#fff;border:1.5px solid #e8e6e0;border-radius:10px;
          padding:1.4rem 1.6rem 0 1.6rem;margin-bottom:0;">
          <div style="font-size:0.84rem;font-weight:700;color:#1a1917;margin-bottom:0.15rem;">
            Sentiment Distribution</div>
          <div style="font-size:0.72rem;color:#8a8680;margin-bottom:0.5rem;">
            Across all analyzed calls</div>
        </div>
        """, unsafe_allow_html=True)
        sent = df["sentiment"].value_counts().reset_index()
        sent.columns = ["Sentiment", "Count"]
        cmap = {"Positive":"#166534","Negative":"#991b1b","Mixed":"#b45309","Neutral":"#6b7280"}
        fig = px.bar(sent, x="Sentiment", y="Count", color="Sentiment",
                     color_discrete_map=cmap, text="Count")
        fig.update_traces(textposition="outside", marker_line_width=0, textfont_size=12)
        fig.update_layout(showlegend=False, **_chart_base())
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown("""
        <div style="background:#fff;border:1.5px solid #e8e6e0;border-radius:10px;
          padding:1.4rem 1.6rem 0 1.6rem;">
          <div style="font-size:0.84rem;font-weight:700;color:#1a1917;margin-bottom:0.15rem;">
            Lead Quality</div>
          <div style="font-size:0.72rem;color:#8a8680;margin-bottom:0.5rem;">
            Hot / Warm / Cold distribution</div>
        </div>
        """, unsafe_allow_html=True)
        lead = df["lead_type"].value_counts().reset_index()
        lead.columns = ["Lead", "Count"]
        lmap = {"Hot":"#991b1b","Warm":"#b45309","Cold":"#1c4ed8"}
        fig2 = px.pie(lead, names="Lead", values="Count", color="Lead",
                      color_discrete_map=lmap, hole=0.58)
        fig2.update_traces(textfont_size=12, textinfo="percent+label",
                           marker=dict(line=dict(color="#fff", width=2)))
        fig2.update_layout(showlegend=True, **_chart_base())
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ──────────────────────────────────────────────────────────────
# TABLE
# ──────────────────────────────────────────────────────────────
def render_table_section(df):
    st.markdown("""
    <div style="font-size:0.84rem;font-weight:700;color:#1a1917;margin-bottom:0.75rem;">
      All Calls</div>
    """, unsafe_allow_html=True)

    s_col, _ = st.columns([5, 4])
    with s_col:
        search = st.text_input("", placeholder="🔍  Search by company, objection, issue…",
                               label_visibility="collapsed", key="search")

    fdf = df.copy()
    if search:
        m = (fdf["id"].str.contains(search, case=False, na=False) |
             fdf["company"].str.contains(search, case=False, na=False) |
             fdf["key_issue"].str.contains(search, case=False, na=False) |
             fdf["top_objection"].str.contains(search, case=False, na=False))
        fdf = fdf[m]

    st.markdown(f'<div style="font-size:0.72rem;color:#8a8680;margin-bottom:0.65rem;">'
                f'{len(fdf)} of {len(df)} calls</div>', unsafe_allow_html=True)

    if fdf.empty:
        st.info("No calls match your search.")
        return

    rows = ""
    for _, r in fdf.head(60).iterrows():
        obj = str(r.get("top_objection", "—"))
        nxt = str(r.get("next_step", "—"))
        rows += f"""
        <tr style="border-bottom:1px solid #f5f4f0;">
          <td style="padding:11px 16px;font-weight:600;color:#1a1917;white-space:nowrap;">{r['id']}</td>
          <td style="padding:11px 16px;color:#4b4845;">{r['company']}</td>
          <td style="padding:11px 16px;">{sent_pill(r.get('sentiment','—'))}</td>
          <td style="padding:11px 16px;">{lead_pill(r.get('lead_type','—'))}</td>
          <td style="padding:11px 16px;color:#4b4845;max-width:240px;line-height:1.4;">{obj}</td>
          <td style="padding:11px 16px;color:#4b4845;max-width:220px;line-height:1.4;">{nxt}</td>
        </tr>"""

    st.markdown(f"""
    <div style="background:#fff;border:1.5px solid #e8e6e0;border-radius:10px;
      overflow:hidden;margin-bottom:1.5rem;">
      <table style="width:100%;border-collapse:collapse;font-size:0.82rem;">
        <thead>
          <tr style="background:#fafaf8;border-bottom:1.5px solid #e8e6e0;">
            <th style="padding:10px 16px;text-align:left;font-size:0.63rem;font-weight:700;
              color:#8a8680;text-transform:uppercase;letter-spacing:0.1em;white-space:nowrap;">Call ID</th>
            <th style="padding:10px 16px;text-align:left;font-size:0.63rem;font-weight:700;
              color:#8a8680;text-transform:uppercase;letter-spacing:0.1em;">Company</th>
            <th style="padding:10px 16px;text-align:left;font-size:0.63rem;font-weight:700;
              color:#8a8680;text-transform:uppercase;letter-spacing:0.1em;">Sentiment</th>
            <th style="padding:10px 16px;text-align:left;font-size:0.63rem;font-weight:700;
              color:#8a8680;text-transform:uppercase;letter-spacing:0.1em;">Lead</th>
            <th style="padding:10px 16px;text-align:left;font-size:0.63rem;font-weight:700;
              color:#8a8680;text-transform:uppercase;letter-spacing:0.1em;">Key Objection</th>
            <th style="padding:10px 16px;text-align:left;font-size:0.63rem;font-weight:700;
              color:#8a8680;text-transform:uppercase;letter-spacing:0.1em;">Next Step</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

    if len(fdf) > 60:
        st.caption(f"Showing first 60 of {len(fdf)} results.")

    render_detail(fdf)

# ──────────────────────────────────────────────────────────────
# CALL DETAIL
# ──────────────────────────────────────────────────────────────
def render_detail(df):
    st.markdown("""
    <div style="height:0.5rem;"></div>
    <div style="font-size:0.84rem;font-weight:700;color:#1a1917;margin-bottom:0.2rem;">
      Call Detail</div>
    <div style="font-size:0.72rem;color:#8a8680;margin-bottom:0.8rem;">
      Select a call to see the full transcript, AI analysis, recommended actions, 
      and generate a follow-up email.</div>
    """, unsafe_allow_html=True)

    sel = st.selectbox("", df["id"].tolist(), label_visibility="collapsed", key="detail_sel")
    r   = df[df["id"] == sel].iloc[0]

    def chip(label, val, fg, bg):
        return f"""<div style="background:{bg};border-radius:8px;padding:0.85rem 1.1rem;">
          <div style="font-size:0.62rem;font-weight:700;color:{fg}88;text-transform:uppercase;
            letter-spacing:0.1em;margin-bottom:0.2rem;">{label}</div>
          <div style="font-size:0.88rem;font-weight:700;color:{fg};">{val}</div>
        </div>"""

    sent_fg, sent_bg = SENT_COLORS.get(r.get("sentiment","Neutral"), ("#4b5563","#f3f4f6"))
    lead_fg, lead_bg = LEAD_COLORS.get(r.get("lead_type","Cold"), ("#1e40af","#eff3ff"))

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(chip("Sentiment",  r.get("sentiment","—"),         sent_fg, sent_bg), unsafe_allow_html=True)
    with c2: st.markdown(chip("Lead Type",  r.get("lead_type","—"),          lead_fg, lead_bg), unsafe_allow_html=True)
    with c3: st.markdown(chip("Resolution", r.get("resolution_status","—"), "#1a1917","#fafaf8"), unsafe_allow_html=True)
    with c4: st.markdown(chip("Agent Score", f"{r.get('rep_score','—')}/5",  "#1a1917","#fafaf8"), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["📄 Transcript", "🧠 AI Insights", "✅ Actions", "✉️ Follow-up Email"])

    # ── Transcript
    with t1:
        content = str(r.get("content", "No transcript available."))
        display = (content
                   .replace("**Sales Rep**",  "<strong style='color:#1c4ed8;'>🎙 Agent</strong>")
                   .replace("**Customer**",   "<strong style='color:#166534;'>👤 Customer</strong>")
                   .replace("\n", "<br>"))
        st.markdown(f"""
        <div style="background:#fafaf8;border:1.5px solid #e8e6e0;border-radius:10px;
          padding:1.4rem 1.8rem;font-size:0.83rem;color:#4b4845;line-height:2;
          max-height:380px;overflow-y:auto;">{display}</div>
        """, unsafe_allow_html=True)

    # ── AI Insights
    with t2:
        ia, ib = st.columns(2)

        def dp(label, val):
            return f"""<div style="background:#fff;border:1.5px solid #e8e6e0;border-radius:10px;
              padding:1rem 1.3rem;margin-bottom:0.7rem;">
              <div style="font-size:0.62rem;font-weight:700;color:#8a8680;text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:0.3rem;">{label}</div>
              <div style="font-size:0.85rem;color:#1a1917;line-height:1.65;">{val}</div>
            </div>"""

        with ia:
            st.markdown(dp("Summary",       r.get("summary","—")),       unsafe_allow_html=True)
            st.markdown(dp("Sentiment Arc", r.get("sentiment_arc","—")), unsafe_allow_html=True)
            st.markdown(dp("Key Issue",     r.get("key_issue","—")),     unsafe_allow_html=True)

        with ib:
            st.markdown(dp("Top Objection", r.get("top_objection","—")), unsafe_allow_html=True)
            st.markdown(dp("Call Outcome",  r.get("outcome","—")),       unsafe_allow_html=True)
            rep_score = r.get("rep_score", 0)
            try: rep_score = int(rep_score)
            except: rep_score = 0
            st.markdown(f"""
            <div style="background:#fff;border:1.5px solid #e8e6e0;border-radius:10px;
              padding:1rem 1.3rem;margin-bottom:0.7rem;">
              <div style="font-size:0.62rem;font-weight:700;color:#8a8680;text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:0.35rem;">Agent Performance</div>
              <div style="margin-bottom:0.35rem;">{score_dots(rep_score)}</div>
              <div style="font-size:0.85rem;color:#1a1917;line-height:1.65;">
                {r.get('rep_score_reason','—')}</div>
            </div>
            """, unsafe_allow_html=True)

        q = str(r.get("standout_quote", ""))
        if q and q != "—":
            st.markdown(f"""
            <div style="border-left:3px solid #1c4ed8;padding:0.75rem 1.1rem;background:#eff3ff;
              border-radius:0 8px 8px 0;font-style:italic;color:#4b4845;font-size:0.85rem;margin-top:0.4rem;">
              "{q}"
            </div>
            """, unsafe_allow_html=True)

    # ── Actions
    with t3:
        ns = str(r.get("next_step", ""))
        if ns and ns != "—":
            st.markdown(f"""
            <div style="background:#eff3ff;border:1.5px solid #bfdbfe;border-left:4px solid #1c4ed8;
              border-radius:0 10px 10px 0;padding:1rem 1.3rem;margin-bottom:1rem;">
              <div style="font-size:0.62rem;font-weight:700;color:#1d4ed8;text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:0.3rem;">Immediate Next Step</div>
              <div style="font-size:0.9rem;font-weight:600;color:#1e3a8a;line-height:1.6;">{ns}</div>
            </div>
            """, unsafe_allow_html=True)

        actions = r.get("recommended_actions", [])
        if isinstance(actions, str):
            import json as _j
            try: actions = _j.loads(actions)
            except: actions = [actions]

        if actions:
            items_html = ""
            for i, a in enumerate(actions, 1):
                items_html += f"""
                <div style="display:flex;gap:0.75rem;align-items:flex-start;
                  padding:0.75rem 0;border-bottom:1px solid #f5f4f0;
                  font-size:0.84rem;color:#1a1917;line-height:1.55;">
                  <div style="min-width:22px;height:22px;background:#eff3ff;color:#1c4ed8;
                    font-weight:700;font-size:0.7rem;border-radius:50%;display:flex;
                    align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;">{i}</div>
                  <div>{a}</div>
                </div>"""
            st.markdown(f"""
            <div style="background:#fff;border:1.5px solid #e8e6e0;border-radius:10px;
              padding:0.4rem 1.2rem 0.4rem;">
              <div style="font-size:0.62rem;font-weight:700;color:#8a8680;text-transform:uppercase;
                letter-spacing:0.1em;padding-top:0.7rem;margin-bottom:0.1rem;">Recommended Actions</div>
              {items_html}
            </div>
            """, unsafe_allow_html=True)

    # ── Follow-up Email
    with t4:
        ek = f"email_{sel}"
        if ek not in st.session_state:
            st.session_state[ek] = None

        if st.session_state[ek] is None:
            st.markdown("""
            <div style="font-size:0.83rem;color:#6b6860;margin-bottom:1.3rem;line-height:1.7;">
              Generate a personalized follow-up email referencing the customer's issue,
              call outcome, and agreed next steps.
            </div>
            """, unsafe_allow_html=True)
            _, bc, _ = st.columns([2, 3, 2])
            with bc:
                if st.button("Generate Follow-up Email", key=f"gen_{sel}"):
                    with st.spinner("Writing email…"):
                        email = generate_email(
                            customer_name=str(r.get("customer_name", "Customer")),
                            summary=str(r.get("summary", "")),
                            key_issue=str(r.get("key_issue", "")),
                            resolution_status=str(r.get("resolution_status", "")),
                            next_step=str(r.get("next_step", "")),
                            order_or_ref=str(r.get("order_or_ref", "N/A")),
                            sentiment=str(r.get("sentiment", "")),
                            call_type=str(r.get("call_type", "")),
                        )
                    st.session_state[ek] = email
                    st.rerun()
        else:
            st.markdown(f"""
            <div style="background:#fafaf8;border:1.5px solid #e8e6e0;border-radius:10px;
              padding:1.4rem 1.8rem;font-size:0.87rem;color:#1a1917;line-height:1.9;
              white-space:pre-wrap;">{st.session_state[ek]}</div>
            """, unsafe_allow_html=True)
            ca, cb_col, _ = st.columns([3, 2, 4])
            with ca:
                st.code(st.session_state[ek], language=None)
            with cb_col:
                if st.button("Regenerate", key=f"regen_{sel}"):
                    st.session_state[ek] = None
                    st.rerun()

# ──────────────────────────────────────────────────────────────
# ROUTER
# ──────────────────────────────────────────────────────────────
stage = st.session_state["stage"]
if   stage == "home":      render_home()
elif stage == "loading":   render_loading()
elif stage == "dashboard": render_dashboard()
else:
    st.session_state["stage"] = "home"
    st.rerun()
