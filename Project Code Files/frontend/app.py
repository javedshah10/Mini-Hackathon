import json
import os
import time

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
LANG_OPTIONS = {"Hindi": "hin", "Bengali": "ben", "Telugu": "tel"}

st.set_page_config(page_title="AI Document Verification Demo", layout="wide")
st.title("AI Document Verification Platform — Phase 1 Demo")

with st.sidebar:
    st.subheader("Backend")
    st.code(BACKEND_URL)

st.header("Screen 1 — Upload")
language_label = st.selectbox("Select document language", list(LANG_OPTIONS.keys()))
file = st.file_uploader("Upload PDF / JPEG / PNG", type=["pdf", "jpg", "jpeg", "png"])

if "submission_id" not in st.session_state:
    st.session_state.submission_id = None

if st.button("Submit"):
    if not file:
        st.error("Please upload a document first.")
    else:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {"language": LANG_OPTIONS[language_label]}
        resp = requests.post(f"{BACKEND_URL}/submit", files=files, params=data, timeout=60)
        if resp.ok:
            payload = resp.json()
            st.session_state.submission_id = payload["submission_id"]
            st.success(f"Uploaded. Submission ID: {payload['submission_id']}")
        else:
            st.error(resp.text)

if st.session_state.submission_id and st.button("Process"):
    with st.spinner("Triggering pipeline..."):
        resp = requests.post(f"{BACKEND_URL}/process/{st.session_state.submission_id}", timeout=120)
        st.write(resp.json() if resp.ok else resp.text)

st.info("Polling status indicator: backend poller runs every POLLING_INTERVAL_SECONDS. Check API logs for pickup counts.")

st.header("Screen 2 — Processing")
progress_placeholder = st.empty()
progress_placeholder.markdown("OCR → Field Extraction → Classification → Validation → Stamp & Signature → Logging")

st.header("Screen 3 — Result")
result_id = st.text_input("Submission ID for result lookup", value=st.session_state.submission_id or "")
if st.button("Fetch Result") and result_id:
    resp = requests.get(f"{BACKEND_URL}/result/{result_id}", timeout=60)
    if not resp.ok:
        st.error(resp.text)
    else:
        data = resp.json()
        st.subheader(f"Overall Status: {str(data.get('status', '')).upper()}")

        validation = data.get("validation_result") or {}
        field_results = (validation.get("field_results") or {}) if isinstance(validation, dict) else {}
        rows = []
        for field_name, details in field_results.items():
            if isinstance(details, dict):
                rows.append(
                    {
                        "field": field_name,
                        "value": details.get("value", json.dumps(details)),
                        "status": details.get("status", "info"),
                    }
                )
            else:
                rows.append({"field": field_name, "value": str(details), "status": "info"})

        if rows:
            st.table(pd.DataFrame(rows))

        with st.expander("Raw JSON output"):
            st.json(data)
