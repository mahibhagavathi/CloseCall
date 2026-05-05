"""
analyzer.py  —  CloseCall AI analysis layer
Uses Groq LLaMA 3.3 70B.
analyze_batch accepts a plain Python callback, NOT a Streamlit widget.
"""
import json
import streamlit as st
from groq import Groq

# ── Prompts ───────────────────────────────────────────────────────────────────

ANALYSIS_PROMPT = """You are an expert customer-service quality analyst. Analyze the support call transcript below and return ONLY a valid JSON object. No markdown fences, no commentary outside the JSON.

STRICT RULES:
- "lead_type"  must be exactly one of: Hot | Warm | Cold
- "outcome"    must be exactly one of: Resolved | Follow-up Needed | Escalated | Unresolved
- "rep_score"  must be an integer 1–5 (no quotes)
- Every string field must be non-empty (use "None raised" or "—" rather than "")
- "recommended_actions" must be a JSON array of exactly 3 strings

Return this exact JSON:
{{
  "summary":             "<2-sentence plain-English summary>",
  "sentiment_arc":       "<one sentence — how customer mood changed through the call>",
  "lead_type":           "<Hot|Warm|Cold>",
  "key_issue":           "<full sentence — main customer problem>",
  "rep_score":           <1|2|3|4|5>,
  "rep_score_reason":    "<one sentence — why this score>",
  "top_objection":       "<main concern raised, or 'None raised'>",
  "outcome":             "<Resolved|Follow-up Needed|Escalated|Unresolved>",
  "next_step":           "<one concrete action the agent must take next>",
  "recommended_actions": ["<action 1>", "<action 2>", "<action 3>"],
  "standout_quote":      "<most revealing verbatim customer quote, or '—'>"
}}

Transcript:
{transcript}"""

EMAIL_PROMPT = """You are a senior customer service representative at Amazon India.
Write a professional follow-up email after a support call.

CALL DETAILS:
- Customer name (first name): {first_name}
- Call reference ID: {call_id}
- Product: {product_name}
- Issue: {key_issue}
- Resolution: {resolution_status}
- Next step: {next_step}
- Customer sentiment: {sentiment}
- CSAT given: {csat}/5
- Agent name: {agent_name}

EMAIL STRUCTURE (follow exactly — separate each section with a blank line):

Subject: [specific helpful subject — NOT generic]

Dear {first_name},

[2 sentences: Thank them for calling. Name the specific product and issue.]

[Resolution paragraph:
  IF resolved/refund/replacement: Confirm exactly what was done. End with: "Share your feedback here: https://amazon.in/feedback/{call_id}"
  IF unresolved/pending/escalated: Apologize sincerely. Give 2–3 numbered concrete steps.]

[1–2 sentences: Clear next steps with any timeline.]

[1 sentence: Warm offer to help further.]

Warm regards,
{agent_name}
Amazon Customer Service

RULES: No "I hope this finds you well". No "As discussed". If CSAT 1–2, open with apology.
Total 160–220 words. Return ONLY the email — no commentary."""


# ── Groq client ───────────────────────────────────────────────────────────────

def get_groq_client() -> Groq:
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except Exception:
        st.error("⚠️ GROQ_API_KEY not found. Go to Streamlit → Settings → Secrets.")
        st.stop()


def _fallback(msg: str) -> dict:
    return {
        "summary":             "Analysis unavailable — please retry.",
        "sentiment_arc":       msg,
        "lead_type":           "Cold",
        "key_issue":           "Could not analyze this transcript.",
        "rep_score":           3,
        "rep_score_reason":    msg,
        "top_objection":       "None raised",
        "outcome":             "Unresolved",
        "next_step":           "Review transcript manually and follow up.",
        "recommended_actions": ["Review transcript manually.", "Follow up with the customer.", "Escalate if needed."],
        "standout_quote":      "—",
    }


def _validate(d: dict) -> dict:
    if d.get("lead_type") not in {"Hot", "Warm", "Cold"}:
        d["lead_type"] = "Cold"
    if d.get("outcome") not in {"Resolved", "Follow-up Needed", "Escalated", "Unresolved"}:
        d["outcome"] = "Unresolved"
    try:
        d["rep_score"] = max(1, min(5, int(d.get("rep_score", 3))))
    except (TypeError, ValueError):
        d["rep_score"] = 3
    actions = d.get("recommended_actions", [])
    if isinstance(actions, str):
        try: actions = json.loads(actions)
        except: actions = [actions]
    d["recommended_actions"] = [str(a) for a in (actions if isinstance(actions, list) else [actions])]
    return d


# ── Public API ────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def analyze_transcript(transcript_content: str, call_id: str) -> dict:
    client = get_groq_client()
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": ANALYSIS_PROMPT.format(transcript=transcript_content)}],
            temperature=0.05,
            max_tokens=800,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return _validate(json.loads(raw.strip()))
    except json.JSONDecodeError as e:
        return _fallback(f"JSON parse error: {e}")
    except Exception as e:
        return _fallback(str(e))


@st.cache_data(show_spinner=False)
def generate_email(
    customer_name: str,
    call_id: str,
    key_issue: str,
    resolution_status: str,
    next_step: str,
    sentiment: str,
    product_name: str,
    agent_name: str,
    csat: int,
) -> str:
    client = get_groq_client()
    first_name = (customer_name or "").split()[0] or "there"
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": EMAIL_PROMPT.format(
                first_name        = first_name,
                call_id           = call_id,
                product_name      = product_name or "the product",
                key_issue         = key_issue,
                resolution_status = resolution_status,
                next_step         = next_step,
                sentiment         = sentiment,
                csat              = csat or "—",
                agent_name        = agent_name or "Support Agent",
            )}],
            temperature=0.3,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not generate email: {e}"


def analyze_batch(transcripts: list, progress_callback=None) -> list:
    """
    Analyze a list of call dicts.
    progress_callback(i, total, call_id) is a PLAIN function — not a Streamlit widget.
    """
    results = []
    total = len(transcripts)
    for i, t in enumerate(transcripts):
        analysis = analyze_transcript(t["content"], t["id"])
        results.append({**t, **analysis})
        if progress_callback is not None:
            progress_callback(i, total, t.get("id", f"call-{i+1}"))
    return results
