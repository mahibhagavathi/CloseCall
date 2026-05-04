cat > /home/claude/sales-intelligence/app.py << 'ENDOFFILE'
import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_sample_transcripts, load_csv_transcripts
from analyzer import analyze_batch, generate_email

# ──────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CloseCall",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Geist', sans-serif !important;
}
.stApp { background: #f8f9fb; }

/* ── Hide chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #21262d !important;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }
section[data-testid="stSidebar"] * { color: #8b949e; }

/* ── Sidebar select/multiselect ── */
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="select"] > div:hover {
    background: #161b22 !important;
    border-color: #30363d !important;
    color: #e6edf3 !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] { background: #1f6feb !important; }
[data-testid="stSidebar"] span { color: #e6edf3 !important; }

/* ── Streamlit buttons ── */
.stButton > button {
    background: #1f6feb !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.6rem 1.5rem !important;
    width: 100% !important;
    letter-spacing: 0.01em !important;
    transition: all 0.15s !important;
    box-shadow: 0 1px 3px rgba(31,111,235,0.3) !important;
}
.stButton > button:hover {
    background: #388bfd !important;
    box-shadow: 0 3px 10px rgba(31,111,235,0.4) !important;
    transform: translateY(-1px) !important;
}

/* ── Progress ── */
.stProgress > div > div { background: #1f6feb !important; }
[data-testid="stProgressBarText"] {
    color: #0d1117 !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid #e2e8f0 !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    color: #64748b !important;
    padding: 0.6rem 1.2rem !important;
    border-radius: 0 !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] {
    color: #1f6feb !important;
    border-bottom: 2px solid #1f6feb !important;
    background: transparent !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] section {
    background: #fff !important;
    border: 2px dashed #cbd5e1 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #1f6feb !important;
    background: #f0f7ff !important;
}

/* ── Text input / select ── */
div[data-testid="stTextInput"] input {
    border-radius: 8px !important;
    border: 1.5px solid #e2e8f0 !important;
    font-size: 0.875rem !important;
    background: #fff !important;
    padding: 0.5rem 0.8rem !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #1f6feb !important;
    box-shadow: 0 0 0 3px rgba(31,111,235,0.1) !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #fff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 1.2rem 1.4rem !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #1f6feb !important; }

/* ── Tooltip ── */
div[data-baseweb="tooltip"] { font-family: 'Geist', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────
DEFAULTS = {
    "stage": "home",          # home | loading | dashboard
    "results_df": None,
    "total_fetched": 0,
    "source_label": "",
    "step_idx": 0,
    "_pending_transcripts": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────────────────────────
# DESIGN HELPERS
# ──────────────────────────────────────────────────────────────
SENT_COLORS = {
    "Positive": ("#059669", "#ecfdf5"),
    "Negative": ("#dc2626", "#fef2f2"),
    "Mixed":    ("#d97706", "#fffbeb"),
    "Neutral":  ("#475569", "#f1f5f9"),
}
LEAD_COLORS = {
    "Hot":  ("#dc2626", "#fef2f2"),
    "Warm": ("#d97706", "#fffbeb"),
    "Cold": ("#2563eb", "#eff6ff"),
}

def pill(text, fg, bg):
    return (f'<span style="display:inline-block;background:{bg};color:{fg};'
            f'border-radius:6px;padding:2px 10px;font-size:0.7rem;font-weight:700;'
            f'letter-spacing:0.05em;text-transform:uppercase;">{text}</span>')

def sent_pill(v):
    fg, bg = SENT_COLORS.get(v, ("#475569","#f1f5f9"))
    return pill(v, fg, bg)

def lead_pill(v):
    fg, bg = LEAD_COLORS.get(v, ("#2563eb","#eff6ff"))
    return pill(v, fg, bg)

def score_dots(n):
    try: n = int(n)
    except: n = 0
    html = ""
    for i in range(1, 6):
        c = "#1f6feb" if i <= n else "#e2e8f0"
        html += f'<span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:{c};margin-right:4px;"></span>'
    return html

def card(content, border_top="transparent", padding="1.4rem 1.6rem"):
    return f"""<div style="background:#fff;border:1px solid #e2e8f0;border-top:3px solid {border_top};
border-radius:14px;padding:{padding};margin-bottom:0;">{content}</div>"""

def section_title(t, sub=""):
    sub_html = f'<div style="font-size:0.76rem;color:#94a3b8;margin-top:0.15rem;">{sub}</div>' if sub else ""
    return f'<div style="font-size:0.9rem;font-weight:700;color:#0f172a;margin-bottom:{"0.2rem" if sub else "0.8rem"}">{t}</div>{sub_html}'

# ──────────────────────────────────────────────────────────────
# SIDEBAR  (only in dashboard stage)
# ──────────────────────────────────────────────────────────────
def render_sidebar_dashboard(df_all):
    with st.sidebar:
        st.markdown("""
        <div style="padding:1.8rem 1rem 1rem 1rem;border-bottom:1px solid #21262d;margin-bottom:1.4rem;">
          <div style="font-family:'Instrument Serif',serif;font-size:1.8rem;color:#e6edf3;letter-spacing:-0.02em;line-height:1;">
            Close<span style="color:#1f6feb;">Call</span>
          </div>
          <div style="font-size:0.68rem;font-weight:600;color:#30363d;text-transform:uppercase;letter-spacing:0.14em;margin-top:0.3rem;">
            Sales Intelligence
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:0.68rem;font-weight:700;color:#30363d;text-transform:uppercase;letter-spacing:0.12em;padding:0 1rem;margin-bottom:0.8rem;">Filters</div>', unsafe_allow_html=True)

        companies  = sorted(df_all["company"].dropna().unique().tolist())
        sentiments = sorted(df_all["sentiment"].dropna().unique().tolist())
        leads      = sorted(df_all["lead_type"].dropna().unique().tolist())
        outcomes   = sorted(df_all["outcome"].dropna().unique().tolist())

        sel_co   = st.multiselect("Company",   companies,  default=companies,  key="f_co")
        sel_sent = st.multiselect("Sentiment", sentiments, default=sentiments, key="f_sent")
        sel_lead = st.multiselect("Lead Type", leads,      default=leads,      key="f_lead")
        sel_out  = st.multiselect("Outcome",   outcomes,   default=outcomes,   key="f_out")

        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
        if st.button("Reset Filters", key="reset"):
            for k in ["f_co","f_sent","f_lead","f_out"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown('<hr style="border-color:#21262d;margin:1rem 0;">', unsafe_allow_html=True)
        if st.button("← New Analysis", key="new_analysis"):
            for k in list(DEFAULTS.keys()) + ["f_co","f_sent","f_lead","f_out"]:
                st.session_state.pop(k, None)
            st.cache_data.clear()
            st.rerun()

        st.markdown(f"""
        <div style="padding:0.8rem 1rem;font-size:0.72rem;color:#30363d;line-height:1.7;">
          {st.session_state.source_label}<br>Groq · LLaMA 3.3 70B
        </div>
        """, unsafe_allow_html=True)

    # Apply filters
    df = df_all.copy()
    if sel_co:   df = df[df["company"].isin(sel_co)]
    if sel_sent: df = df[df["sentiment"].isin(sel_sent)]
    if sel_lead: df = df[df["lead_type"].isin(sel_lead)]
    if sel_out:  df = df[df["outcome"].isin(sel_out)]
    return df

# ──────────────────────────────────────────────────────────────
# HOME PAGE
# ──────────────────────────────────────────────────────────────
def render_home():
    with st.sidebar:
        st.markdown("""
        <div style="padding:1.8rem 1rem 1rem 1rem;border-bottom:1px solid #21262d;margin-bottom:1.4rem;">
          <div style="font-family:'Instrument Serif',serif;font-size:1.8rem;color:#e6edf3;letter-spacing:-0.02em;">
            Close<span style="color:#1f6feb;">Call</span>
          </div>
          <div style="font-size:0.68rem;font-weight:600;color:#30363d;text-transform:uppercase;letter-spacing:0.14em;margin-top:0.3rem;">Sales Intelligence</div>
        </div>
        <div style="padding:0 1rem;font-size:0.8rem;color:#6e7681;line-height:2;">
          <div>📊&nbsp; Sentiment analysis</div>
          <div>🔥&nbsp; Lead scoring (Hot / Warm / Cold)</div>
          <div>💬&nbsp; Objection detection</div>
          <div>⭐&nbsp; Rep performance scoring</div>
          <div>✉️&nbsp; AI follow-up email writer</div>
          <div>📋&nbsp; Recommended actions</div>
        </div>
        """, unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div style="padding:3rem 0 2.5rem 0;">
      <div style="font-family:'Instrument Serif',serif;font-size:3.4rem;color:#0f172a;letter-spacing:-0.03em;line-height:1.1;margin-bottom:1rem;">
        Turn calls into<br><span style="color:#1f6feb;">pipeline intelligence</span>
      </div>
      <div style="font-size:1rem;color:#64748b;max-width:520px;line-height:1.7;">
        Paste in your transcripts or use our sample dataset.
        CloseCall uses AI to extract sentiment, objections, lead quality, 
        rep scores, and writes follow-up emails — in seconds.
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_a, spacer, col_b = st.columns([11, 1, 11])

    with col_a:
        st.markdown("""
        <div style="background:#fff;border:1.5px solid #e2e8f0;border-radius:16px;padding:2rem;margin-bottom:1rem;">
          <div style="font-size:1.8rem;margin-bottom:0.8rem;">📂</div>
          <div style="font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:0.4rem;">Upload Your Transcripts</div>
          <div style="font-size:0.83rem;color:#64748b;line-height:1.65;margin-bottom:1.2rem;">
            Drop a CSV file with a <code style="background:#f1f5f9;padding:1px 5px;border-radius:4px;">transcript</code> or 
            <code style="background:#f1f5f9;padding:1px 5px;border-radius:4px;">content</code> column.<br>
            Optional: <code style="background:#f1f5f9;padding:1px 5px;border-radius:4px;">id</code> and 
            <code style="background:#f1f5f9;padding:1px 5px;border-radius:4px;">company</code> columns.
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

    with spacer:
        st.markdown("""
        <div style="display:flex;align-items:center;justify-content:center;height:260px;">
          <div style="width:1px;height:140px;background:#e2e8f0;position:relative;">
            <span style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
              background:#f8f9fb;color:#94a3b8;font-size:0.72rem;font-weight:600;
              padding:4px 0;white-space:nowrap;">or</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div style="background:#fff;border:1.5px solid #e2e8f0;border-radius:16px;padding:2rem;margin-bottom:1rem;">
          <div style="font-size:1.8rem;margin-bottom:0.8rem;">🗂️</div>
          <div style="font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:0.4rem;">Use Sample Dataset</div>
          <div style="font-size:0.83rem;color:#64748b;line-height:1.65;margin-bottom:1.2rem;">
            100 sales call transcripts across fashion, real estate,
            finance, healthcare &amp; tech. Ready to analyze — no upload needed.
          </div>
          <div style="display:flex;gap:0.6rem;flex-wrap:wrap;">
            <span style="background:#f0f7ff;color:#1f6feb;border-radius:20px;padding:3px 12px;font-size:0.72rem;font-weight:600;">100 calls</span>
            <span style="background:#f0fdf4;color:#059669;border-radius:20px;padding:3px 12px;font-size:0.72rem;font-weight:600;">10 companies</span>
            <span style="background:#fff7ed;color:#d97706;border-radius:20px;padding:3px 12px;font-size:0.72rem;font-weight:600;">5 industries</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Analyze Sample Dataset  →", key="btn_sample"):
            with st.spinner("Fetching transcripts..."):
                transcripts = load_sample_transcripts()
            _start_analysis(transcripts, f"Sample dataset · {len(transcripts)} calls")

def _start_analysis(transcripts, label):
    st.session_state["_pending_transcripts"] = transcripts
    st.session_state["total_fetched"] = len(transcripts)
    st.session_state["source_label"] = label
    st.session_state["stage"] = "loading"
    st.rerun()

# ──────────────────────────────────────────────────────────────
# LOADING PAGE  (step progress bar)
# ──────────────────────────────────────────────────────────────
def render_loading():
    transcripts = st.session_state.get("_pending_transcripts", [])
    if not transcripts:
        st.session_state["stage"] = "home"
        st.rerun()
        return

    total = len(transcripts)

    _, col, _ = st.columns([1, 5, 1])
    with col:
        st.markdown(f"""
        <div style="padding:4rem 0 2rem 0; text-align:center;">
          <div style="font-family:'Instrument Serif',serif;font-size:2.2rem;color:#0f172a;margin-bottom:0.5rem;">
            Analyzing {total} calls
          </div>
          <div style="font-size:0.9rem;color:#64748b;margin-bottom:2.5rem;">
            CloseCall is reading each transcript and extracting insights using Groq LLaMA 3.3
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Step indicators
        steps = ["Fetching transcripts", "Analyzing with AI", "Building insights"]
        step_html = '<div style="display:flex;justify-content:center;gap:0;margin-bottom:2rem;">'
        for i, s in enumerate(steps):
            is_done    = i < 1
            is_active  = i == 1
            dot_bg     = "#1f6feb" if (is_done or is_active) else "#e2e8f0"
            txt_color  = "#0f172a" if (is_done or is_active) else "#94a3b8"
            line_color = "#1f6feb" if is_done else "#e2e8f0"
            dot_inner  = "✓" if is_done else str(i+1)
            step_html += f"""
            <div style="display:flex;align-items:center;">
              <div style="text-align:center;min-width:100px;">
                <div style="width:32px;height:32px;border-radius:50%;background:{dot_bg};
                  color:#fff;font-size:0.8rem;font-weight:700;display:flex;
                  align-items:center;justify-content:center;margin:0 auto 0.4rem auto;">{dot_inner}</div>
                <div style="font-size:0.72rem;font-weight:600;color:{txt_color};">{s}</div>
              </div>
              {"" if i==len(steps)-1 else f'<div style="width:60px;height:2px;background:{line_color};margin:0 0.3rem 1.2rem 0.3rem;"></div>'}
            </div>"""
        step_html += "</div>"
        st.markdown(step_html, unsafe_allow_html=True)

        progress = st.progress(0, text="Starting...")

    def cb(i, total, label):
        pct = (i + 1) / total
        # Update step indicator: step 2 active while processing
        progress.progress(pct, text=f"Analyzing call {i+1} of {total} — {label}")

    results = analyze_batch(transcripts, cb)
    progress.empty()

    st.session_state["results_df"] = pd.DataFrame(results)
    st.session_state["stage"] = "dashboard"
    st.session_state["_pending_transcripts"] = None
    st.rerun()

# ──────────────────────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────────────────────
def render_dashboard():
    df_all = st.session_state["results_df"]
    total_fetched = st.session_state["total_fetched"]
    df = render_sidebar_dashboard(df_all)

    # Page header
    total_shown = len(df)
    sampling_note = ""
    if total_shown < len(df_all):
        sampling_note = f" · Filtered to {total_shown} of {len(df_all)}"
    elif len(df_all) < total_fetched:
        sampling_note = f" · Showing {len(df_all)} of {total_fetched}"

    st.markdown(f"""
    <div style="padding:1.8rem 0 2rem 0;border-bottom:1px solid #e2e8f0;margin-bottom:2rem;">
      <div style="font-family:'Instrument Serif',serif;font-size:2.2rem;color:#0f172a;letter-spacing:-0.02em;line-height:1;">
        Close<span style="color:#1f6feb;">Call</span>
      </div>
      <div style="font-size:0.78rem;color:#94a3b8;margin-top:0.35rem;font-weight:500;">
        {st.session_state['source_label']}{sampling_note}
      </div>
    </div>
    """, unsafe_allow_html=True)

    render_kpis(df, total_fetched)
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    render_charts(df)
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    render_table_section(df)

# ──────────────────────────────────────────────────────────────
# KPI ROW
# ──────────────────────────────────────────────────────────────
def render_kpis(df, total_fetched):
    n = len(df)
    pos  = len(df[df["sentiment"] == "Positive"])
    neg  = len(df[df["sentiment"] == "Negative"])
    hot  = len(df[df["lead_type"] == "Hot"])
    pos_pct = round(pos/n*100) if n else 0
    neg_pct = round(neg/n*100) if n else 0
    sampled_note = f"of {total_fetched} total" if n < total_fetched else "all calls"

    k1, k2, k3, k4 = st.columns(4)
    for col, accent, label, big, sub in [
        (k1, "#1f6feb", "Calls Analyzed",     str(n),         sampled_note),
        (k2, "#059669", "Positive Sentiment", f"{pos_pct}%",  f"{pos} calls"),
        (k3, "#dc2626", "Negative Sentiment", f"{neg_pct}%",  f"{neg} calls"),
        (k4, "#f59e0b", "Hot Leads",          str(hot),       "high intent"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #e2e8f0;border-top:3px solid {accent};
              border-radius:14px;padding:1.4rem 1.6rem;">
              <div style="font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:0.5rem;">{label}</div>
              <div style="font-size:2.4rem;font-weight:800;color:#0f172a;line-height:1;
                letter-spacing:-0.03em;">{big}</div>
              <div style="font-size:0.72rem;color:#94a3b8;margin-top:0.35rem;">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# CHARTS
# ──────────────────────────────────────────────────────────────
def _chart_base():
    return dict(
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        font=dict(family="Geist, sans-serif", color="#64748b", size=11),
        margin=dict(l=8, r=8, t=36, b=8),
        xaxis=dict(gridcolor="#f1f5f9", zerolinecolor="#f1f5f9", title=None),
        yaxis=dict(gridcolor="#f1f5f9", zerolinecolor="#f1f5f9", title=None),
    )

def render_charts(df):
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:1.4rem 1.6rem 0.6rem 1.6rem;margin-bottom:0;">
          <div style="font-size:0.85rem;font-weight:700;color:#0f172a;margin-bottom:0.1rem;">Sentiment Distribution</div>
          <div style="font-size:0.73rem;color:#94a3b8;margin-bottom:0.8rem;">Across all analyzed calls</div>
        </div>
        """, unsafe_allow_html=True)
        sent = df["sentiment"].value_counts().reset_index()
        sent.columns = ["Sentiment", "Count"]
        cmap = {"Positive":"#059669","Negative":"#dc2626","Mixed":"#d97706","Neutral":"#94a3b8"}
        fig = px.bar(sent, x="Sentiment", y="Count", color="Sentiment",
                     color_discrete_map=cmap, text="Count")
        fig.update_traces(textposition="outside", marker_line_width=0, textfont_size=13)
        fig.update_layout(showlegend=False, **_chart_base())
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown("""
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:1.4rem 1.6rem 0.6rem 1.6rem;">
          <div style="font-size:0.85rem;font-weight:700;color:#0f172a;margin-bottom:0.1rem;">Lead Quality Breakdown</div>
          <div style="font-size:0.73rem;color:#94a3b8;margin-bottom:0.8rem;">Hot / Warm / Cold distribution</div>
        </div>
        """, unsafe_allow_html=True)
        lead = df["lead_type"].value_counts().reset_index()
        lead.columns = ["Lead", "Count"]
        lmap = {"Hot":"#dc2626","Warm":"#d97706","Cold":"#2563eb"}
        fig2 = px.pie(lead, names="Lead", values="Count", color="Lead",
                      color_discrete_map=lmap, hole=0.55)
        fig2.update_traces(textfont_size=12, textinfo="percent+label",
                           marker=dict(line=dict(color="#fff", width=2)))
        fig2.update_layout(showlegend=True, **_chart_base())
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ──────────────────────────────────────────────────────────────
# TABLE + DETAIL
# ──────────────────────────────────────────────────────────────
def render_table_section(df):
    st.markdown("""
    <div style="font-size:0.85rem;font-weight:700;color:#0f172a;margin-bottom:0.8rem;">All Calls</div>
    """, unsafe_allow_html=True)

    s_col, _ = st.columns([5, 3])
    with s_col:
        search = st.text_input("", placeholder="🔍  Search by company, issue, objection…",
                               label_visibility="collapsed", key="search")

    fdf = df.copy()
    if search:
        m = (fdf["id"].str.contains(search, case=False, na=False) |
             fdf["company"].str.contains(search, case=False, na=False) |
             fdf["key_issue"].str.contains(search, case=False, na=False) |
             fdf["top_objection"].str.contains(search, case=False, na=False))
        fdf = fdf[m]

    st.markdown(f'<div style="font-size:0.74rem;color:#94a3b8;margin-bottom:0.7rem;">{len(fdf)} of {len(df)} calls</div>',
                unsafe_allow_html=True)

    if fdf.empty:
        st.info("No calls match your search.")
        return

    rows = ""
    for _, r in fdf.head(60).iterrows():
        obj = str(r.get("top_objection","—"))
        rows += f"""
        <tr style="border-bottom:1px solid #f1f5f9;">
          <td style="padding:12px 16px;font-weight:600;color:#0f172a;white-space:nowrap;">{r['id']}</td>
          <td style="padding:12px 16px;color:#475569;">{r['company']}</td>
          <td style="padding:12px 16px;">{sent_pill(r.get('sentiment','—'))}</td>
          <td style="padding:12px 16px;">{lead_pill(r.get('lead_type','—'))}</td>
          <td style="padding:12px 16px;color:#475569;max-width:260px;line-height:1.4;">{obj}</td>
          <td style="padding:12px 16px;color:#475569;max-width:240px;line-height:1.4;">{str(r.get('next_step','—'))}</td>
        </tr>"""

    st.markdown(f"""
    <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;margin-bottom:1.5rem;">
      <table style="width:100%;border-collapse:collapse;font-size:0.83rem;">
        <thead>
          <tr style="background:#f8f9fb;border-bottom:1px solid #e2e8f0;">
            <th style="padding:10px 16px;text-align:left;font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;white-space:nowrap;">Call ID</th>
            <th style="padding:10px 16px;text-align:left;font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;">Company</th>
            <th style="padding:10px 16px;text-align:left;font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;">Sentiment</th>
            <th style="padding:10px 16px;text-align:left;font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;">Lead</th>
            <th style="padding:10px 16px;text-align:left;font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;">Key Objection</th>
            <th style="padding:10px 16px;text-align:left;font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;">Next Step</th>
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
    <div style="font-size:0.85rem;font-weight:700;color:#0f172a;margin-bottom:0.2rem;">Call Detail</div>
    <div style="font-size:0.74rem;color:#94a3b8;margin-bottom:0.8rem;">Select a call for full transcript, AI analysis, actions, and follow-up email.</div>
    """, unsafe_allow_html=True)

    sel = st.selectbox("", df["id"].tolist(), label_visibility="collapsed", key="detail_sel")
    r = df[df["id"] == sel].iloc[0]

    # Meta chips row
    def chip(label, val, fg, bg):
        return f"""<div style="background:{bg};border-radius:10px;padding:0.9rem 1.2rem;">
          <div style="font-size:0.65rem;font-weight:700;color:{fg}99;text-transform:uppercase;letter-spacing:0.09em;margin-bottom:0.25rem;">{label}</div>
          <div style="font-size:0.9rem;font-weight:700;color:{fg};">{val}</div>
        </div>"""

    sent_fg, sent_bg = SENT_COLORS.get(r.get("sentiment","Neutral"), ("#475569","#f1f5f9"))
    lead_fg, lead_bg = LEAD_COLORS.get(r.get("lead_type","Cold"), ("#2563eb","#eff6ff"))

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(chip("Sentiment",  r.get("sentiment","—"),         sent_fg, sent_bg), unsafe_allow_html=True)
    with c2: st.markdown(chip("Lead Type",  r.get("lead_type","—"),          lead_fg, lead_bg), unsafe_allow_html=True)
    with c3: st.markdown(chip("Resolution", r.get("resolution_status","—"), "#0f172a","#f8f9fb"), unsafe_allow_html=True)
    with c4: st.markdown(chip("Rep Score",  f"{r.get('rep_score','—')}/5",  "#0f172a","#f8f9fb"), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["📄 Transcript", "🧠 AI Insights", "✅ Actions", "✉️ Follow-up Email"])

    # ── Transcript
    with t1:
        content = str(r.get("content","No transcript available."))
        display = (content
                   .replace("**Sales Rep**","<strong style='color:#1f6feb;'>🎙 Sales Rep</strong>")
                   .replace("**Customer**","<strong style='color:#059669;'>👤 Customer</strong>")
                   .replace("\n","<br>"))
        st.markdown(f"""
        <div style="background:#f8f9fb;border:1px solid #e2e8f0;border-radius:12px;
          padding:1.4rem 1.8rem;font-size:0.83rem;color:#475569;line-height:2;
          max-height:380px;overflow-y:auto;">{display}</div>
        """, unsafe_allow_html=True)

    # ── AI Insights
    with t2:
        ia, ib = st.columns(2)
        def dp(label, val):
            return f"""<div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;
              padding:1.1rem 1.4rem;margin-bottom:0.75rem;">
              <div style="font-size:0.65rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:0.35rem;">{label}</div>
              <div style="font-size:0.87rem;color:#0f172a;line-height:1.6;">{val}</div>
            </div>"""

        with ia:
            st.markdown(dp("Summary",       r.get("summary","—")), unsafe_allow_html=True)
            st.markdown(dp("Sentiment Arc", r.get("sentiment_arc","—")), unsafe_allow_html=True)
            st.markdown(dp("Key Issue",     r.get("key_issue","—")), unsafe_allow_html=True)
        with ib:
            st.markdown(dp("Top Objection", r.get("top_objection","—")), unsafe_allow_html=True)
            st.markdown(dp("Sales Outcome", r.get("outcome","—")), unsafe_allow_html=True)
            rep_score = r.get("rep_score", 0)
            try: rep_score = int(rep_score)
            except: rep_score = 0
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;
              padding:1.1rem 1.4rem;margin-bottom:0.75rem;">
              <div style="font-size:0.65rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:0.4rem;">Rep Performance</div>
              <div style="margin-bottom:0.4rem;">{score_dots(rep_score)}</div>
              <div style="font-size:0.87rem;color:#0f172a;line-height:1.6;">{r.get('rep_score_reason','—')}</div>
            </div>
            """, unsafe_allow_html=True)
        q = str(r.get("standout_quote",""))
        if q and q != "—":
            st.markdown(f"""
            <div style="border-left:3px solid #1f6feb;padding:0.7rem 1rem;background:#f0f7ff;
              border-radius:0 10px 10px 0;font-style:italic;color:#475569;font-size:0.86rem;margin-top:0.5rem;">
              "{q}"
            </div>
            """, unsafe_allow_html=True)

    # ── Actions
    with t3:
        ns = str(r.get("next_step",""))
        if ns and ns != "—":
            st.markdown(f"""
            <div style="background:#eff6ff;border:1px solid #bfdbfe;border-left:4px solid #1f6feb;
              border-radius:0 12px 12px 0;padding:1.1rem 1.4rem;margin-bottom:1rem;">
              <div style="font-size:0.65rem;font-weight:700;color:#1d4ed8;text-transform:uppercase;
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
                <div style="display:flex;gap:0.8rem;align-items:flex-start;padding:0.8rem 0;
                  border-bottom:1px solid #f1f5f9;font-size:0.86rem;color:#0f172a;line-height:1.5;">
                  <div style="min-width:24px;height:24px;background:#eff6ff;color:#1f6feb;
                    font-weight:700;font-size:0.72rem;border-radius:50%;display:flex;
                    align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;">{i}</div>
                  <div>{a}</div>
                </div>"""
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;
              padding:0.5rem 1.2rem 0.5rem 1.2rem;">
              <div style="font-size:0.65rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:0.1rem;padding-top:0.7rem;">Recommended Actions</div>
              {items_html}
            </div>
            """, unsafe_allow_html=True)

    # ── Email
    with t4:
        ek = f"email_{sel}"
        if ek not in st.session_state:
            st.session_state[ek] = None

        if st.session_state[ek] is None:
            st.markdown(f"""
            <div style="font-size:0.84rem;color:#64748b;margin-bottom:1.2rem;line-height:1.6;">
              Generate a personalized follow-up email addressed to the customer by name,
              referencing their issue, order details, and agreed next steps.
            </div>
            """, unsafe_allow_html=True)
            _, bc, _ = st.columns([2,3,2])
            with bc:
                if st.button("Generate Follow-up Email", key=f"gen_{sel}"):
                    with st.spinner("Writing personalized email…"):
                        email = generate_email(
                            customer_name=str(r.get("customer_name","Customer")),
                            summary=str(r.get("summary","")),
                            key_issue=str(r.get("key_issue","")),
                            resolution_status=str(r.get("resolution_status","")),
                            next_step=str(r.get("next_step","")),
                            order_or_ref=str(r.get("order_or_ref","N/A")),
                            sentiment=str(r.get("sentiment","")),
                            call_type=str(r.get("call_type","")),
                        )
                    st.session_state[ek] = email
                    st.rerun()
        else:
            st.markdown(f"""
            <div style="background:#f8f9fb;border:1px solid #e2e8f0;border-radius:12px;
              padding:1.4rem 1.8rem;font-size:0.88rem;color:#0f172a;line-height:1.9;
              white-space:pre-wrap;">{st.session_state[ek]}</div>
            """, unsafe_allow_html=True)
            ca, cb, _ = st.columns([3,2,4])
            with ca:
                st.code(st.session_state[ek], language=None)
            with cb:
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
ENDOFFILE
