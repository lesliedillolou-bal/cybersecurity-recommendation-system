from pathlib import Path
import sys
import uuid

import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))
from utils import apply_app_theme
from storage import load_profile, save_profile

st.set_page_config(page_title="Security Profile", page_icon="🧩", layout="wide")
apply_app_theme()
st.title("🧩 Security Profile")
st.write("Set the context that should guide your review of defensive recommendations.")
st.caption("Do not enter passwords, API keys, confidential incident details, or other sensitive information.")

if "app_session_id" not in st.session_state:
    st.session_state["app_session_id"] = uuid.uuid4().hex
if "security_profile_loaded" not in st.session_state:
    saved_profile = load_profile(st.session_state["app_session_id"])
    if saved_profile:
        st.session_state["security_profile"] = saved_profile
    st.session_state["security_profile_loaded"] = True

current = st.session_state.get("security_profile", {})
with st.form("security_profile_form"):
    environment_options = ["Cloud", "On-premises", "Hybrid", "Small business / home lab", "Not sure yet"]
    size_options = ["Personal / learning lab", "Small team", "Medium organization", "Large organization", "Prefer not to say"]
    priority_options = [
        "Vulnerability management", "Endpoint protection", "Cloud security", "Network security",
        "Identity and access management", "Security monitoring", "Incident response readiness",
        "Security awareness and learning", "Compliance support"
    ]
    constraint_options = [
        "Limited budget", "Small IT/security team", "Prefer open-source tools",
        "Need simple deployment", "Need cloud-native options", "Need to align with existing controls"
    ]
    environment = st.selectbox(
        "Primary environment", environment_options,
        index=environment_options.index(current["environment"]) if current.get("environment") in environment_options else 0,
    )
    organization_size = st.selectbox(
        "Environment size", size_options,
        index=size_options.index(current["organization_size"]) if current.get("organization_size") in size_options else 0,
    )
    priorities = st.multiselect(
        "Main defensive priorities", priority_options,
        default=[item for item in current.get("priorities", ["Vulnerability management"]) if item in priority_options],
    )
    constraints = st.multiselect(
        "Practical constraints", constraint_options,
        default=[item for item in current.get("constraints", []) if item in constraint_options],
    )
    maturity_options = ["Learning / starting", "Basic", "Developing", "Established", "Advanced"]
    maturity = st.select_slider(
        "Current security program maturity", options=maturity_options,
        value=current.get("maturity", "Learning / starting") if current.get("maturity") in maturity_options else "Learning / starting",
    )
    submitted = st.form_submit_button("Save profile", type="primary")

if submitted:
    profile = {
        "environment": environment,
        "organization_size": organization_size,
        "priorities": priorities,
        "constraints": constraints,
        "maturity": maturity,
    }
    try:
        save_profile(st.session_state["app_session_id"], profile)
        st.session_state["security_profile"] = profile
        st.success("Profile saved to this deployment's local database.")
    except Exception as exc:
        st.error(f"Could not persist profile: {type(exc).__name__}: {exc}")
        st.session_state["security_profile"] = profile
        st.info("The profile remains available for this active session.")

profile = st.session_state.get("security_profile")
if profile:
    st.subheader("Current profile")
    st.json(profile)
else:
    st.info("Complete the form to save a profile and personalize the defensive tool/control catalog.")

st.caption(
    "Storage note: the profile is keyed to an anonymous Streamlit session ID and stored locally. "
    "It is not sent to catalog sources. Session IDs may change when a new session starts, and ephemeral hosting "
    "may not preserve local files across redeployments. Do not use this prototype for sensitive profiles."
)
