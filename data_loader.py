import requests
import pandas as pd
import streamlit as st
import io

HF_API_URL = "https://huggingface.co/api/datasets/gwenshap/sales-transcripts/tree/main/data/transcripts"
HF_RAW_BASE = "https://huggingface.co/datasets/gwenshap/sales-transcripts/raw/main/data/transcripts"


@st.cache_data(show_spinner=False)
def fetch_file_list() -> list[str]:
    """Fetch all transcript filenames from HuggingFace (handles pagination)."""
    files = []
    url = HF_API_URL
    while url:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        for item in data:
            path = item.get("path", "")
            if path.endswith("_transcript.txt"):
                files.append(path.split("/")[-1])
        # HuggingFace may paginate via Link header
        link = resp.headers.get("Link", "")
        if 'rel="next"' in link:
            import re
            match = re.search(r'<([^>]+)>;\s*rel="next"', link)
            url = match.group(1) if match else None
        else:
            url = None
    return files


@st.cache_data(show_spinner=False)
def fetch_transcript(filename: str) -> str:
    url = f"{HF_RAW_BASE}/{filename}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_meta(filename: str) -> tuple[str, str]:
    """Return (company, call_index) from filename like modamart__0_transcript.txt"""
    base = filename.replace("_transcript.txt", "")
    parts = base.split("__")
    company = parts[0].replace("-", " ").title() if parts else "Unknown"
    idx = parts[1] if len(parts) > 1 else "0"
    return company, idx


def load_sample_transcripts() -> list[dict]:
    """Load all transcripts from HuggingFace. Returns list of dicts."""
    file_list = fetch_file_list()
    transcripts = []
    for fname in file_list:
        company, idx = parse_meta(fname)
        try:
            content = fetch_transcript(fname)
        except Exception as e:
            content = f"[Load error: {e}]"
        transcripts.append({
            "filename": fname,
            "company": company,
            "index": idx,
            "content": content,
            "id": f"{company} #{idx}",
            "source": "sample",
        })
    return transcripts


def load_csv_transcripts(uploaded_file) -> list[dict]:
    """Parse a user-uploaded CSV into transcript dicts."""
    df = pd.read_csv(uploaded_file)
    df.columns = [c.strip().lower() for c in df.columns]

    # Find transcript column
    candidate_cols = ["transcript", "content", "text", "conversation", "call", "dialogue", "body"]
    transcript_col = next((c for c in candidate_cols if c in df.columns), None)
    if transcript_col is None:
        # Fall back to largest text column
        text_cols = df.select_dtypes(include="object").columns.tolist()
        if not text_cols:
            raise ValueError("No text columns found in CSV.")
        transcript_col = max(text_cols, key=lambda c: df[c].astype(str).str.len().mean())

    # Find optional id/company columns
    id_col = next((c for c in ["id", "call_id", "call id"] if c in df.columns), None)
    company_col = next((c for c in ["company", "org", "client"] if c in df.columns), None)

    transcripts = []
    for i, row in df.iterrows():
        content = str(row[transcript_col])
        call_id = str(row[id_col]) if id_col else f"Call #{i+1}"
        company = str(row[company_col]) if company_col else "Uploaded"
        transcripts.append({
            "filename": call_id,
            "company": company,
            "index": str(i),
            "content": content,
            "id": call_id,
            "source": "upload",
        })
    return transcripts
