from pathlib import Path
import sys
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))
st.set_page_config(page_title="Security Profile", page_icon="🧩", layout="wide")
st.title("🧩 Security Profile")
st.write("Set the context that should guide your review of defensive recommendations.")
st.caption("Do not enter passwords, API keys, confidential incident details, or other sensitive information.")

with st.form("security_profile_form"):
    environment = st.selectbox("Primary environment", ["Cloud","On-premises","Hybrid","Small business / home lab","Not sure yet"])
    organization_size = st.selectbox("Environment size", ["Personal / learning lab","Small team","Medium organization","Large organization","Prefer not to say"])
    priorities = st.multiselect("Main defensive priorities", [
        "Vulnerability management","Endpoint protection","Cloud security","Network security",
        "Identity and access management","Security monitoring","Incident response readiness",
        "Security awareness and learning","Compliance support"
    ], default=["Vulnerability management"])
    constraints = st.multiselect("Practical constraints", [
        "Limited budget","Small IT/security team","Prefer open-source tools",
        "Need simple deployment","Need cloud-native options","Need to align with existing controls"
    ])
    maturity = st.select_slider("Current security program maturity",
        options=["Learning / starting","Basic","Developing","Established","Advanced"], value="Learning / starting")
    submitted = st.form_submit_button("Save profile for this session", type="primary")

if submitted:
    st.session_state["security_profile"] = {
        "environment":environment, "organization_size":organization_size,
        "priorities":priorities, "constraints":constraints, "maturity":maturity
    }
    st.success("Profile saved for this browser session.")

profile = st.session_state.get("security_profile")
if profile:
    st.subheader("Current session profile")
    st.json(profile)
    st.info("The current recommender does not yet score catalog records against every profile field. This profile captures requirements for the next tool/control-catalog phase.")
else:
    st.info("No profile saved yet. Complete the form above to keep your preferences in this session.")
