from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
from utils import apply_app_theme, load_catalog

st.set_page_config(
    page_title="Cybersecurity Intelligence Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_app_theme()

st.markdown(
    """
    <section class="cyber-hero">
      <div class="cyber-chip">DEFENSIVE SECURITY · RESEARCH PROTOTYPE</div>
      <h1>Cybersecurity Intelligence</h1>
      <p>Turn vulnerability catalog data into clearer security priorities. Explore CISA Known Exploited Vulnerabilities, compare similar records, and review practical defensive controls in one workspace.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

df, source_label, load_error = load_catalog()
if load_error:
    st.warning(load_error)

if df.empty:
    st.error("The vulnerability catalog is unavailable right now.")
    st.markdown(
        "You can still open the other pages from the sidebar. Live catalog recommendations require "
        "the cleaned dataset or access to the official CISA feed."
    )
    st.stop()

st.markdown('<div class="cyber-eyebrow">Live catalog overview</div>', unsafe_allow_html=True)
st.caption(f"Data source: {source_label}")

vendors = df.loc[df["vendor"].astype(str).str.strip().ne(""), "vendor"]
products = df.loc[df["product"].astype(str).str.strip().ne(""), "product"]
required_actions = int(df["required_action"].astype(str).str.strip().ne("").sum())
cols = st.columns(4)
cols[0].metric("Vulnerability records", f"{len(df):,}")
cols[1].metric("Unique vendors", f"{vendors.nunique():,}")
cols[2].metric("Unique products", f"{products.nunique():,}")
cols[3].metric("Records with required action", f"{required_actions:,}")

st.markdown("---")
st.markdown('<div class="cyber-eyebrow">Threat catalog insights</div>', unsafe_allow_html=True)
left, right = st.columns([1, 1], gap="large")

with left:
    if vendors.size:
        top = vendors.value_counts().head(10)
        plot_df = top.rename_axis("Vendor").reset_index(name="Records").sort_values("Records")
        chart = px.bar(
            plot_df, x="Records", y="Vendor", orientation="h",
            title="Vendors most represented in KEV",
            color="Records", color_continuous_scale=["#155e75", "#2dd4bf"],
        )
        chart.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#dbe7f5", title_font_size=17,
            coloraxis_showscale=False, margin=dict(l=8, r=8, t=54, b=8),
            xaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,.12)", zeroline=False),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info("Vendor metadata is not available for charting.")

with right:
    if df["date_added"].notna().any():
        monthly = (
            df.dropna(subset=["date_added"])
            .assign(Month=lambda frame: frame["date_added"].dt.strftime("%Y-%m"))
            .groupby("Month", as_index=False).size()
            .rename(columns={"size": "Records"})
        )
        chart = px.line(monthly, x="Month", y="Records", markers=True, title="KEV records by month added")
        chart.update_traces(line_color="#2dd4bf", marker_color="#60a5fa", line_width=3)
        chart.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#dbe7f5", title_font_size=17,
            margin=dict(l=8, r=8, t=54, b=8),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,.12)", zeroline=False),
        )
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info("No parseable date-added values are available.")

st.markdown("---")
latest_col, note_col = st.columns([1.65, 1], gap="large")
with latest_col:
    st.subheader("Recently added records")
    recent = df.sort_values("date_added", ascending=False, na_position="last").head(8)
    columns = [column for column in ["cve_id", "vendor", "product", "vulnerability_name", "date_added"] if column in recent.columns]
    st.dataframe(recent[columns], use_container_width=True, hide_index=True)
with note_col:
    st.subheader("How to use this workspace")
    st.markdown(
        """
        **01 · Set context**  
        Describe your environment and defensive priorities.

        **02 · Explore recommendations**  
        Inspect similar vulnerability records and general controls.

        **03 · Evaluate results**  
        Compare rankings against independent human judgments.

        **04 · Review and export**  
        Record feedback and export research outputs.
        """
    )
    st.info("Use the sidebar to open each workspace page.")

st.caption(
    "Research note: catalog similarity is not a substitute for security assessment or expert review. "
    "CISA KEV is a vulnerability catalog, not a commercial tool rating source."
)
