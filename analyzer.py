import json
import streamlit as st
from groq import Groq

ANALYSIS_PROMPT = """You are an expert sales analyst. Analyze this sales call transcript and return ONLY a valid JSON object — no markdown, no backticks, no explanation.

CRITICAL RULES — follow these exactly:
- "sentiment" MUST be one of these four exact strings: Positive, Negative, Neutral, Mixed
  - Positive = customer was happy or satisfied overall
  - Negative = customer was frustrated, angry, or unhappy overall  
  - Mixed = sentiment changed significantly during the call (started bad ended good, or vice versa)
  - Neutral = no strong emotion either way
  - NEVER return "Unknown" or any other value
- "lead_type" MUST be one of: Hot, Warm, Cold — NEVER "Unknown"
- Every field must be a non-empty string
- "rep_score" must be an integer 1–5

Return exactly this JSON structure:
{{
  "summary": "<2-sentence plain-English summary of what happened on this call>",
  "customer_name": "<customer first name if mentioned, else 'Customer'>",
  "sentiment": "<Positive|Negative|Neutral|Mixed — pick the most accurate one>",
  "sentiment_arc": "<one sentence: how customer emotion changed during the call>",
  "call_type": "<Product Enquiry|Complaint|Troubleshooting|Negotiation|Compliment|Follow-up>",
  "resolution_status": "<Resolved|Unresolved|Escalated|Pending>",
  "lead_type": "<Hot|Warm|Cold>",
  "key_issue": "<complete sentence describing the main customer concern — do not truncate>",
  "rep_score": <1|2|3|4|5>,
  "rep_score_reason": "<one sentence explaining the agent/rep score>",
  "top_objection": "<complete sentence describing main objection raised, or 'No significant objection raised'>",
  "outcome": "<Sale Likely|Sale Unlikely|Neutral|Follow-up Needed>",
  "next_step": "<complete, specific action the rep must take next — full sentence, not abbreviated>",
  "recommended_actions": [
    "<specific action 1 — full sentence>",
    "<specific action 2 — full sentence>",
    "<specific action 3 — full sentence>"
  ],
  "standout_quote": "<most revealing customer quote verbatim from the transcript>"
}}

Transcript:
{transcript}"""


EMAIL_PROMPT = """You are a professional customer service representative writing a follow-up email after a support call.

Call details:
- Customer name: {customer_name}
- Call reference / ID: {order_or_ref}
- Issue discussed: {key_issue}
- Resolution: {resolution_status}
- Agreed next step: {next_step}
- Customer sentiment during call: {sentiment}
- Call type: {call_type}
- Summary: {summary}

Write a complete, professional follow-up email. Requirements:
1. Start with: Dear {customer_name},
2. Reference the call: "Thank you for speaking with us today regarding [issue]."
3. If there is an order/reference number (not N/A), mention it: "Your reference number is [ref]."
4. Summarize what was discussed and the resolution or status
5. State the next steps clearly
6. If sentiment was Positive or Neutral: ask for feedback — "We'd love to hear your feedback at [feedback link]."
7. If sentiment was Negative: sincerely apologize and reaffirm commitment to resolution
8. Close with: "Warm regards,\n[Agent Name]\nCustomer Support Team"

Keep it under 200 words. Warm, professional tone. No filler phrases like "I hope this email finds you well."
Return ONLY the email body — no subject line, no JSON, no extra commentary."""


def get_groq_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except Exception:
        st.error("GROQ_API_KEY not found. Go to Streamlit → Settings → Secrets and add it.")
        st.stop()


def _fallback(msg: str) -> dict:
    return {
        "summary": "Analysis unavailable — please retry.",
        "customer_name": "Customer",
        "sentiment": "Neutral",
        "sentiment_arc": msg,
        "call_type": "Product Enquiry",
        "resolution_status": "Pending",
        "lead_type": "Cold",
        "key_issue": "Could not analyze this transcript. Please retry.",
        "rep_score": 3,
        "rep_score_reason": msg,
        "top_objection": "No significant objection raised",
        "outcome": "Neutral",
        "next_step": "Review transcript manually and follow up with the customer.",
        "recommended_actions": [
            "Review the transcript manually.",
            "Follow up directly with the customer.",
            "Escalate to team lead if needed.",
        ],
        "standout_quote": "—",
    }


def _validate(raw: dict) -> dict:
    """Force all enum fields to valid values — prevents Unknown from appearing."""
    valid_sent = {"Positive", "Negative", "Neutral", "Mixed"}
    valid_lead = {"Hot", "Warm", "Cold"}
    valid_res  = {"Resolved", "Unresolved", "Escalated", "Pending",
                  "Refund Issued", "Replacement Sent", "Partial Resolution", "Callback Scheduled"}
    valid_out  = {"Sale Likely", "Sale Unlikely", "Neutral", "Follow-up Needed"}

    if raw.get("sentiment") not in valid_sent:
        raw["sentiment"] = "Neutral"
    if raw.get("lead_type") not in valid_lead:
        raw["lead_type"] = "Cold"
    if raw.get("outcome") not in valid_out:
        raw["outcome"] = "Neutral"

    # Ensure list fields are actually lists
    actions = raw.get("recommended_actions", [])
    if isinstance(actions, str):
        try:
            actions = json.loads(actions)
        except Exception:
            actions = [actions]
    raw["recommended_actions"] = actions if isinstance(actions, list) else [str(actions)]

    # Ensure integer score
    try:
        raw["rep_score"] = max(1, min(5, int(raw.get("rep_score", 3))))
    except (TypeError, ValueError):
        raw["rep_score"] = 3

    return raw


@st.cache_data(show_spinner=False)
def analyze_transcript(transcript_content: str, transcript_id: str) -> dict:
    client = get_groq_client()
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": ANALYSIS_PROMPT.format(transcript=transcript_content)}],
            temperature=0.05,   # very low temp → more consistent enum values
            max_tokens=800,
        )
        raw_text = resp.choices[0].message.content.strip()
        # Strip markdown fences if model wrapped output
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        result = json.loads(raw_text.strip())
        return _validate(result)
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
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": EMAIL_PROMPT.format(
                customer_name=customer_name,
                order_or_ref=order_or_ref,
                key_issue=key_issue,
                resolution_status=resolution_status,
                next_step=next_step,
                sentiment=sentiment,
                call_type=call_type,
                summary=summary,
            )}],
            temperature=0.35,
            max_tokens=450,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not generate email: {e}"


def analyze_batch(transcripts: list, progress_callback=None) -> list:
    results = []
    total = len(transcripts)
    for i, t in enumerate(transcripts):
        analysis = analyze_transcript(t["content"], t["id"])
        results.append({**t, **analysis})
        if progress_callback is not None:
            progress_callback(i, total, t.get("id", f"call-{i+1}"))
    return results
