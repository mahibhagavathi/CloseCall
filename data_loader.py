"""
data_loader.py
Loads the Amazon India call records from the bundled XLSX file.
Returns a list of dicts — one per call — ready for CloseCall's analyzer.
"""

import pandas as pd
import streamlit as st
import os

# ✅ Robust path (works locally + Streamlit Cloud)
BASE_DIR = os.path.dirname(__file__)
XLSX_PATH = os.path.join(BASE_DIR, "amazon_india_calls.xlsx")

# Map Excel columns → internal names
COL_MAP = {
    "Call ID":                 "id",
    "Timestamp":               "timestamp",
    "Duration (sec)":          "duration_sec",
    "Hold Time (sec)":         "hold_sec",
    "Channel":                 "channel",
    "Call Type":               "call_type_raw",
    "Customer ID":             "customer_id",
    "Customer Name":           "customer_name",
    "Phone Number":            "phone",
    "City":                    "city",
    "State":                   "state",
    "Country":                 "country",
    "Customer Service Agent":  "agent_name",
    "Employee ID":             "employee_id",
    "Agent Experience (Yrs)":  "agent_exp_yrs",
    "Product ID":              "product_id",
    "Product Name":            "product_name",
    "Product Category":        "product_category",
    "Sentiment":               "sentiment_raw",
    "Resolution":              "resolution_raw",
    "First Call Resolution":   "fcr",
    "Transfers":               "transfers",
    "CSAT Score (1-5)":        "csat",
    "Transcript":              "content",
}


@st.cache_data(show_spinner=False)
def load_amazon_transcripts() -> list[dict]:
    # ✅ Check file exists
    if not os.path.exists(XLSX_PATH):
        raise FileNotFoundError(f"Excel file not found at: {XLSX_PATH}")

    # ✅ Load Excel (no sheet dependency)
    df = pd.read_excel(XLSX_PATH)

    # ✅ Clean column names (important)
    df.columns = [c.strip() for c in df.columns]

    # ✅ Rename columns
    df.rename(columns=COL_MAP, inplace=True)

    records = []

    # ✅ LOOP — this is where everything happens
    for _, row in df.iterrows():
        rec = {}

        # Populate fields safely
        for k in COL_MAP.values():
            val = row.get(k)
            rec[k] = val if pd.notna(val) else ""

        # ✅ FIX: Create "sentiment" (THIS WAS YOUR BUG)
        rec["sentiment"] = str(rec.get("sentiment_raw", "")).strip().title()

        # Optional: clean values
        valid = {"Positive", "Negative", "Mixed"}
        if rec["sentiment"] not in valid:
            rec["sentiment"] = "Mixed"

        # Normalize numeric fields
        for num_col in ("duration_sec", "hold_sec", "agent_exp_yrs", "transfers", "csat"):
            try:
                rec[num_col] = int(rec[num_col])
            except (ValueError, TypeError):
                rec[num_col] = 0

        # Duration label (for UI)
        d = rec["duration_sec"]
        rec["duration_label"] = f"{d // 60}m {d % 60}s" if d >= 60 else f"{d}s"

        records.append(rec)

    return records


# ✅ Keep this (your app depends on it)
def load_sample_transcripts() -> list[dict]:
    return load_amazon_transcripts()


def load_csv_transcripts(uploaded_file) -> list[dict]:
    df = pd.read_csv(uploaded_file)
    df.columns = [c.strip().lower() for c in df.columns]

    if "transcript" in df.columns:
        df.rename(columns={"transcript": "content"}, inplace=True)

    if "content" not in df.columns:
        raise ValueError("CSV must contain a 'transcript' or 'content' column.")

    if "id" not in df.columns:
        df["id"] = [f"CALL-{i+1:04d}" for i in range(len(df))]

    # Add missing fields for UI compatibility
    for col in (
        "customer_name", "company", "city", "state",
        "product_category", "channel", "call_type_raw",
        "csat", "duration_label", "sentiment"
    ):
        if col not in df.columns:
            df[col] = ""

    return df.to_dict("records")
