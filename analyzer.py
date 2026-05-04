import json
import streamlit as st
from groq import Groq

ANALYSIS_PROMPT = """You are an expert sales analyst. Analyze this sales call transcript and return ONLY a valid JSON object — no markdown, no backticks, no explanation.

Return exactly this structure:
{{
  "summary": "<2-sentence plain-English summary of the call>",
  "sentiment": "<one of: Positive, Neutral, Negative, Mixed>",
  "sentiment_arc": "<one sentence: how sentiment shifted during the call>",
  "call_type": "<one of: Product Enquiry, Complaint, Troubleshooting, Negotiation, Compliment, Follow-up>",
  "resolution_status": "<one of: Resolved, Unresolved, Escalated, Pending>",
  "lead_type": "<one of: Hot, Warm, Cold>",
  "key_issue": "<one sentence: main customer concern>",
  "rep_score": <integer 1 to 5>,
  "rep_score_reason": "<one sentence explaining the rep score>",
  "top_objection": "<main objection raised, or None>",
  "outcome": "<one of: Sale Likely, Sale Unlikely, Neutral, Follow-up Needed>",
  "next_step": "<one concrete next action the rep should take>",
  "recommended_actions": ["<action 1>", "<action 2>", "<action 3>"],
  "standout_quote": "<most revealing customer quote>"
}}

Lead type guidance:
- Hot = expressed clear buying intent or urgency
- Warm = interested but hesitant, needs nurturing
- Cold = unlikely to convert based on this call

Transcript:
{transcript}"""

EMAIL_PROMPT = """You are a professional sales rep writing a follow-up email after a sales call.

Rules:
- Max 150 words
- Friendly but professional tone
- Reference something specific from the call
- End with a clear call to action
- Do NOT use openers like "I hope this email finds you well"
- Return ONLY the email body text

Call summary: {summary}
Key issue: {key_issue}
Agreed next step: {next_step}
Customer sentiment: {sentiment}

Transcript excerpt:
{transcript_excerpt}"""


def get_groq_client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]
        return Groq(api_key=api_key)
    except Exception:
        st.error("GROQ_API_KEY not found. Add it in Streamlit Settings → Secrets.")
        st.stop()


def _fallback(error_msg: str) -> dict:
    return {
        "summary": "Analysis unavailable.",
        "sentiment": "Unknown",
        "sentiment_arc": error_msg,
        "call_type": "Unknown",
        "resolution_status": "Unknown",
        "lead_type": "Cold",
        "key_issue": "Analysis failed",
        "rep_score": 0,
        "rep_score_reason": error_msg,
        "top_objection": "None",
        "outcome": "Unknown",
        "next_step": "Retry analysis",
        "recommended_actions": ["Check API key and retry"],
        "standout_quote": "—",
    }


@st.cache_data(show_spinner=False)
def analyze_transcript(transcript_content: str, transcript_id: str) -> dict:
    client = get_groq_client()
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": ANALYSIS_PROMPT.format(transcript=transcript_content)}],
            temperature=0.1,
            max_tokens=700,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except json.JSONDecodeError as e:
        return _fallback(f"JSON parse error: {e}")
    except Exception as e:
        return _fallback(str(e))


@st.cache_data(show_spinner=False)
def generate_email(
    customer_name: str,
    summary: str,
    key_issue: str,
    resolution_status: str,
    next_step: str,
    order_or_ref: str,
    sentiment: str,
    call_type: str,
) -> str:
    client = get_groq_client()
    transcript_excerpt = f"Issue: {key_issue}. Resolution: {resolution_status}. Ref: {order_or_ref}."
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": EMAIL_PROMPT.format(
                    summary=summary,
                    key_issue=key_issue,
                    next_step=next_step,
                    sentiment=sentiment,
                    transcript_excerpt=transcript_excerpt[:800],
                ),
            }],
            temperature=0.4,
            max_tokens=300,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not generate email: {e}"


def analyze_batch(transcripts: list, progress_callback=None) -> list:
    """
    Analyze a list of transcripts.
    progress_callback(i, total, call_id) is called after each transcript.
    It is a plain function — NOT a Streamlit widget.
    """
    results = []
    total = len(transcripts)
    for i, t in enumerate(transcripts):
        analysis = analyze_transcript(t["content"], t["id"])
        results.append({**t, **analysis})
        if progress_callback is not None:
            progress_callback(i, total, t.get("id", f"call-{i+1}"))
    return results
