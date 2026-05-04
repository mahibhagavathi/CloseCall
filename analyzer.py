import json
import streamlit as st
from groq import Groq

ANALYSIS_PROMPT = """You are an expert sales call analyst. Analyze the following sales transcript and return ONLY a valid JSON object with no extra text, no markdown, no backticks.

Return exactly this structure:
{{
  "sentiment": "<one of: Positive, Neutral, Negative, Mixed>",
  "sentiment_arc": "<one sentence describing how sentiment changed during the call, e.g. 'Started hesitant, ended confident'>",
  "call_type": "<one of: Product Enquiry, Complaint, Troubleshooting, Negotiation, Compliment, Follow-up>",
  "resolution_status": "<one of: Resolved, Unresolved, Escalated, Pending>",
  "key_issue": "<one sentence describing the main customer concern>",
  "rep_score": <integer 1 to 5>,
  "rep_score_reason": "<one sentence explaining the score>",
  "top_objection": "<main objection raised by customer, or 'None' if no objection>",
  "outcome": "<one of: Sale Likely, Sale Unlikely, Neutral, Follow-up Needed>",
  "standout_quote": "<most revealing customer quote from the transcript>"
}}

Transcript:
{transcript}"""


def get_groq_client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]
        return Groq(api_key=api_key)
    except Exception:
        st.error("GROQ_API_KEY not found in Streamlit secrets. Please add it in Settings → Secrets.")
        st.stop()


@st.cache_data(show_spinner=False)
def analyze_transcript(transcript_content: str, transcript_id: str) -> dict:
    """Analyze a single transcript using Groq LLaMA."""
    client = get_groq_client()
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": ANALYSIS_PROMPT.format(transcript=transcript_content)
                }
            ],
            temperature=0.1,
            max_tokens=600,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except json.JSONDecodeError as e:
        return {
            "sentiment": "Unknown",
            "sentiment_arc": "Parse error",
            "call_type": "Unknown",
            "resolution_status": "Unknown",
            "key_issue": "Analysis failed",
            "rep_score": 0,
            "rep_score_reason": str(e),
            "top_objection": "Unknown",
            "outcome": "Unknown",
            "standout_quote": "—"
        }
    except Exception as e:
        return {
            "sentiment": "Error",
            "sentiment_arc": str(e),
            "call_type": "Error",
            "resolution_status": "Error",
            "key_issue": str(e),
            "rep_score": 0,
            "rep_score_reason": "API error",
            "top_objection": "Error",
            "outcome": "Error",
            "standout_quote": "—"
        }


def analyze_batch(transcripts: list, progress_bar=None) -> list:
    """Analyze a list of transcript dicts and return enriched dicts."""
    results = []
    total = len(transcripts)
    for i, t in enumerate(transcripts):
        analysis = analyze_transcript(t["content"], t["id"])
        results.append({**t, **analysis})
        if progress_bar:
            progress_bar.progress((i + 1) / total, text=f"Analyzing {t['id']}... ({i+1}/{total})")
    return results
