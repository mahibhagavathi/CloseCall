"""
data_loader.py
Loads the Amazon India call records from the bundled XLSX file.
Returns a list of dicts — one per call — ready for CloseCall's analyzer.
"""
import pandas as pd
import streamlit as st

XLSX_PATH = "amazon_india_calls.xlsx"

# Map the Excel columns → internal field names used by the rest of the app
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
    df = pd.read_excel(XLSX_PATH, sheet_name="Call Records")
    df.rename(columns=COL_MAP, inplace=True)

    records = []
    for _, row in df.iterrows():
        rec = {k: (row[k] if pd.notna(row.get(k)) else "") for k in COL_MAP.values()}
        # Normalise numeric fields
        for num_col in ("duration_sec", "hold_sec", "agent_exp_yrs", "transfers", "csat"):
            try:
                rec[num_col] = int(rec[num_col])
            except (ValueError, TypeError):
                rec[num_col] = 0
        # Build a human-readable duration string
        d = rec["duration_sec"]
        rec["duration_label"] = f"{d // 60}m {d % 60}s" if d >= 60 else f"{d}s"
        records.append(rec)

    return records


def load_csv_transcripts(uploaded_file) -> list[dict]:
    """Fallback: accept a user-uploaded CSV with at least a 'transcript'/'content' column."""
    df = pd.read_csv(uploaded_file)
    df.columns = [c.strip().lower() for c in df.columns]
    if "transcript" in df.columns:
        df.rename(columns={"transcript": "content"}, inplace=True)
    if "content" not in df.columns:
        raise ValueError("CSV must contain a 'transcript' or 'content' column.")
    if "id" not in df.columns:
        df["id"] = [f"CALL-{i+1:04d}" for i in range(len(df))]
    for col in ("customer_name", "company", "city", "state", "product_category",
                "channel", "call_type_raw", "csat", "duration_label"):
        if col not in df.columns:
            df[col] = ""
    return df.to_dict("records")
