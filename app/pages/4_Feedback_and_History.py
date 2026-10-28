from datetime import datetime, timezone
from pathlib import Path
import sys
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))
st.set_page_config(page_title="Feedback & History", page_icon="🗂️", layout="wide")
st.title("🗂️ Feedback & History")
st.write("Record your review of recommendations and export this session's history.")
st.caption("Feedback is stored only in the current Streamlit session. It is not sent to a server database.")
if "recommendation_feedback" not in st.session_state:
    st.session_state["recommendation_feedback"] = []

with st.form("feedback_form"):
    item_id = st.text_input("CVE ID or recommendation reference", placeholder="e.g. CVE-2024-0000")
    rating = st.slider("How useful was the recommendation?", min_value=1, max_value=5, value=3)
    outcome = st.selectbox("Review outcome", ["Not reviewed yet","Relevant to my needs","Partly relevant","Not relevant","Needs expert review"])
    notes = st.text_area("Optional notes", placeholder="Avoid entering secrets, personal data, or confidential incident details.")
    submitted = st.form_submit_button("Save feedback", type="primary")

if submitted:
    if not item_id.strip():
        st.error("Enter a CVE ID or reference before saving.")
    else:
        st.session_state["recommendation_feedback"].append({
            "timestamp_utc":datetime.now(timezone.utc).isoformat(),
            "reference":item_id.strip(), "usefulness_rating":int(rating),
            "review_outcome":outcome, "notes":notes.strip()
        })
        st.success("Feedback saved for this session.")

history = st.session_state["recommendation_feedback"]
st.subheader(f"Session history ({len(history)} entries)")
if history:
    history_df = pd.DataFrame(history)
    st.dataframe(history_df, use_container_width=True, hide_index=True)
    st.download_button("Download feedback history as CSV", data=history_df.to_csv(index=False).encode("utf-8"),
        file_name="cybersecurity_recommendation_feedback.csv", mime="text/csv")
    if st.button("Clear this session's feedback"):
        st.session_state["recommendation_feedback"] = []
        st.rerun()
else:
    st.info("No feedback has been recorded in this session yet.")
st.markdown("**Research note:** feedback is not automatically used to train a model. Before using ratings for evaluation or training, define a review protocol, protect privacy, and separate development feedback from held-out test judgments.")
