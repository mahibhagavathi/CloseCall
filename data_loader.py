import requests
import json
import os
import streamlit as st

HF_API_URL = "https://huggingface.co/api/datasets/gwenshap/sales-transcripts/tree/main/data/transcripts"
HF_RAW_BASE = "https://huggingface.co/datasets/gwenshap/sales-transcripts/raw/main/data/transcripts"
CACHE_FILE = "transcripts_cache.json"


@st.cache_data(show_spinner=False)
def fetch_file_list():
    """Fetch list of transcript files from HuggingFace."""
    try:
        resp = requests.get(HF_API_URL, timeout=15)
        resp.raise_for_status()
        files = resp.json()
        return [
            f["path"].split("/")[-1]
            for f in files
            if f["path"].endswith("_transcript.txt")
        ]
    except Exception as e:
        st.error(f"Failed to fetch file list: {e}")
        return []


@st.cache_data(show_spinner=False)
def fetch_transcript(filename: str) -> str:
    """Fetch a single transcript file content."""
    url = f"{HF_RAW_BASE}/{filename}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"Error loading {filename}: {e}"


def parse_company_and_index(filename: str):
    """Extract company name and index from filename like modamart__0_transcript.txt"""
    base = filename.replace("_transcript.txt", "")
    parts = base.split("__")
    company = parts[0].replace("-", " ").title() if len(parts) > 0 else "Unknown"
    idx = parts[1] if len(parts) > 1 else "0"
    return company, idx


def load_all_transcripts():
    """Load all transcripts and return as list of dicts."""
    files = fetch_file_list()
    transcripts = []
    for fname in files:
        company, idx = parse_company_and_index(fname)
        content = fetch_transcript(fname)
        transcripts.append({
            "filename": fname,
            "company": company,
            "index": idx,
            "content": content,
            "id": f"{company} #{idx}"
        })
    return transcripts
