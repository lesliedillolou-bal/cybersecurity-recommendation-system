from datetime import datetime, timezone
from pathlib import Path
import sys
import uuid

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))
from utils import apply_app_theme
from storage import clear_feedback, list_feedback, save_feedback

st.set_page_config(page_title="Feedback & History", page_icon="🗂️", layout="wide")
apply_app_theme()
st.title("🗂️ Feedback & History")
st.write("Record your review of recommendations and export your saved history.")
st.caption("Avoid entering secrets, personal data, or confidential incident details.")

if "app_session_id" not in st.session_state:
    st.session_state["app_session_id"] = uuid.uuid4().hex
session_id = st.session_state["app_session_id"]

with st.form("feedback_form"):
    item_id = st.text_input("CVE ID or recommendation reference", placeholder="e.g. CVE-2024-0000")
    rating = st.slider("How useful was the recommendation?", min_value=1, max_value=5, value=3)
    outcome = st.selectbox(
        "Review outcome",
        ["Not reviewed yet", "Relevant to my needs", "Partly relevant", "Not relevant", "Needs expert review"],
    )
    notes = st.text_area("Optional notes", placeholder="Do not include secrets or sensitive incident details.")
    submitted = st.form_submit_button("Save feedback", type="primary")

if submitted:
    if not item_id.strip():
        st.error("Enter a CVE ID or reference before saving.")
    else:
        entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "reference": item_id.strip(),
            "usefulness_rating": int(rating),
            "review_outcome": outcome,
            "notes": notes.strip(),
        }
        try:
            save_feedback(session_id, entry)
            st.success("Feedback saved to this deployment's local database.")
        except Exception as exc:
            st.error(f"Could not persist feedback: {type(exc).__name__}: {exc}")

try:
    history = list_feedback(session_id)
except Exception as exc:
    history = []
    st.error(f"Could not load saved feedback: {type(exc).__name__}: {exc}")

st.subheader(f"Saved history ({len(history)} entries)")
if history:
    history_df = pd.DataFrame(history)
    st.dataframe(history_df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download feedback history as CSV",
        data=history_df.to_csv(index=False).encode("utf-8"),
        file_name="cybersecurity_recommendation_feedback.csv",
        mime="text/csv",
    )
    if st.button("Clear this session's saved feedback"):
        clear_feedback(session_id)
        st.rerun()
else:
    st.info("No feedback has been recorded for this app session yet.")

st.markdown(
    "**Research note:** feedback is not automatically used to train a model or treated as ground-truth relevance. "
    "Use a documented review protocol and a separate held-out judgment set before calculating recommendation metrics."
)
st.caption(
    "Storage note: entries are scoped to an anonymous Streamlit session ID in the local SQLite database. "
    "This prototype has no login system; local storage may be ephemeral on hosted deployments. "
    "Do not use it for confidential data."
)
