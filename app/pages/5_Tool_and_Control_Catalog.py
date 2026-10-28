from pathlib import Path
import sys

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = APP_DIR.parent
sys.path.insert(0, str(ROOT_DIR))
from src.catalog_recommender import load_control_catalog, load_tool_catalog, recommend_controls, recommend_tools

st.set_page_config(page_title="Tool & Control Catalog", page_icon="🧰", layout="wide")
st.title("🧰 Defensive Tool & Control Catalog")
st.write("Explore a curated starter list of defensive security tools and foundational controls with official source links.")
st.warning(
    "This is a curated starter catalog, not an independent product audit. Match scores reflect tag overlap with your profile, "
    "not measured effectiveness, a security guarantee, or an endorsement. Check current documentation, licensing, costs, and fit before adoption."
)

profile = st.session_state.get("security_profile", {})
if not profile:
    st.info("Tip: save a profile on the Security Profile page to personalize the ordering. Without one, results are alphabetical or foundational.")
else:
    st.caption("Using your current session profile; profile details are not sent to the catalog sources.")

tab_tools, tab_controls = st.tabs(["Defensive tools", "Security controls"])

with tab_tools:
    tools = load_tool_catalog()
    categories = ["All categories"] + sorted(tools["category"].dropna().unique().tolist())
    chosen_category = st.selectbox("Filter by category", categories)
    search = st.text_input("Search tools", placeholder="e.g. endpoint, cloud, network")
    shown = tools.copy()
    if chosen_category != "All categories":
        shown = shown[shown["category"].eq(chosen_category)]
    if search.strip():
        mask = (
            shown["name"].astype(str) + " " + shown["description"].astype(str) + " " +
            shown["priorities"].astype(str) + " " + shown["category"].astype(str)
        ).str.casefold().str.contains(search.strip().casefold(), regex=False, na=False)
        shown = shown.loc[mask]
    ranked = recommend_tools(shown, profile)
    st.caption(f"{len(ranked)} tool(s) in this view")
    for _, tool in ranked.iterrows():
        with st.container(border=True):
            header, score_col = st.columns([5, 1])
            header.subheader(str(tool["name"]))
            header.caption(f'{tool["category"]} · {tool["cost_model"]} · Skill level: {tool["skill_level"]}')
            score_col.metric("Profile match", int(tool["match_score"]) if profile else "—")
            st.write(str(tool["description"]))
            st.write("**Strengths:**", str(tool["strengths"]))
            st.write("**Limitations:**", str(tool["limitations"]))
            st.write("**Deployment:**", str(tool["deployment"]))
            st.write("**Suitable environments:**", str(tool["suitable_environments"]).replace(";", ", "))
            st.write("**Why shown:**", str(tool["match_reasons"]))
            st.markdown(f'[Official project site]({tool["official_url"]}) · [Documentation/source]({tool["source_url"]})')

with tab_controls:
    controls = load_control_catalog()
    control_ranked = recommend_controls(controls, profile)
    categories = ["All categories"] + sorted(controls["category"].dropna().unique().tolist())
    chosen_control_category = st.selectbox("Filter controls by category", categories, key="control_category")
    control_search = st.text_input("Search controls", placeholder="e.g. asset inventory, backups")
    shown_controls = control_ranked.copy()
    if chosen_control_category != "All categories":
        shown_controls = shown_controls[shown_controls["category"].eq(chosen_control_category)]
    if control_search.strip():
        mask = (
            shown_controls["control_name"].astype(str) + " " +
            shown_controls["description"].astype(str) + " " +
            shown_controls["priority_tags"].astype(str)
        ).str.casefold().str.contains(control_search.strip().casefold(), regex=False, na=False)
        shown_controls = shown_controls.loc[mask]
    for _, control in shown_controls.iterrows():
        with st.container(border=True):
            header, score_col = st.columns([5, 1])
            header.subheader(str(control["control_name"]))
            header.caption(f'{control["category"]} · Effort estimate: {control["effort"]}')
            score_col.metric("Profile match", int(control["match_score"]) if profile else "—")
            st.write(str(control["description"]))
            st.write("**Why it matters:**", str(control["why_it_matters"]))
            st.write("**Why shown:**", str(control["match_reasons"]))
            st.markdown(f'[Source: {control["source_name"]}]({control["official_source"]})')
    st.caption("Effort is a qualitative starter estimate, not a sourced cost quote. Validate requirements for your organization.")
