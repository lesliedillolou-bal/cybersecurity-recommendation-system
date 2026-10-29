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


def style_chart(chart, *, height=330, show_legend=False):
    """Apply a consistent, low-noise dark style to dashboard charts."""
    chart.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd8e8", family="Inter, ui-sans-serif, system-ui", size=12),
        title=dict(font=dict(color="#f3f7ff", size=16), x=0.02, xanchor="left"),
        margin=dict(l=10, r=12, t=52, b=12),
        height=height,
        showlegend=show_legend,
        hoverlabel=dict(
            bgcolor="#111c2f",
            bordercolor="rgba(45,212,191,.5)",
            font=dict(color="#f3f7ff", size=12),
        ),
    )
    chart.update_xaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,.12)",
        zeroline=False,
        linecolor="rgba(148,163,184,.18)",
        ticks="outside",
        tickcolor="rgba(148,163,184,.22)",
    )
    chart.update_yaxes(
        showgrid=False,
        zeroline=False,
        linecolor="rgba(148,163,184,.18)",
    )
    return chart


st.markdown(
    """
    <section class="cyber-hero">
      <div class="cyber-chip">DEFENSIVE SECURITY · RESEARCH PROTOTYPE</div>
      <h1>Cybersecurity Intelligence</h1>
      <p>Turn vulnerability catalog data into clearer security priorities. Explore CISA Known Exploited Vulnerabilities, compare similar records, and review practical defensive controls in one workspace.</p>
      <div style="display:flex;flex-wrap:wrap;gap:9px;margin-top:20px;">
        <span style="border:1px solid rgba(45,212,191,.22);background:rgba(45,212,191,.08);border-radius:9px;padding:7px 10px;color:#a7f3e8;font-size:12px;">◈ Vulnerability intelligence</span>
        <span style="border:1px solid rgba(96,165,250,.22);background:rgba(96,165,250,.08);border-radius:9px;padding:7px 10px;color:#bfdbfe;font-size:12px;">↗ Evidence-led prioritization</span>
        <span style="border:1px solid rgba(148,163,184,.2);background:rgba(148,163,184,.06);border-radius:9px;padding:7px 10px;color:#cbd5e1;font-size:12px;">⌁ Defensive research workspace</span>
      </div>
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

st.markdown('<div class="cyber-eyebrow">01 / Catalog overview</div>', unsafe_allow_html=True)
st.caption(f"Data source · {source_label}")

vendors = df.loc[df["vendor"].astype(str).str.strip().ne(""), "vendor"]
products = df.loc[df["product"].astype(str).str.strip().ne(""), "product"]
required_actions = int(df["required_action"].astype(str).str.strip().ne("").sum())
action_coverage = (required_actions / len(df) * 100) if len(df) else 0
metric_cols = st.columns(4)
metric_cols[0].metric("Vulnerability records", f"{len(df):,}", help="Unique CVE records in the loaded catalog.")
metric_cols[1].metric("Vendors represented", f"{vendors.nunique():,}", help="Distinct non-empty vendor names.")
metric_cols[2].metric("Products represented", f"{products.nunique():,}", help="Distinct non-empty product names.")
metric_cols[3].metric(
    "Records with action guidance",
    f"{required_actions:,}",
    help=f"{action_coverage:.1f}% of loaded records have a non-empty required-action field.",
)

st.markdown("---")
st.markdown('<div class="cyber-eyebrow">02 / Threat catalog insights</div>', unsafe_allow_html=True)
st.markdown("### Explore the shape of the catalog")
st.caption("These charts summarize the loaded CISA KEV records; they are descriptive views, not risk scores or product ratings.")

left, right = st.columns(2, gap="large")
with left:
    with st.container(border=True):
        st.markdown("**Vendor concentration**")
        st.caption("Vendors with the most records in the current catalog.")
        if vendors.size:
            top_vendors = vendors.value_counts().head(10)
            plot_df = top_vendors.rename_axis("Vendor").reset_index(name="Records").sort_values("Records")
            chart = px.bar(
                plot_df,
                x="Records",
                y="Vendor",
                orientation="h",
                color="Records",
                color_continuous_scale=["#164e63", "#0d9488", "#5eead4"],
                text="Records",
            )
            chart.update_traces(
                textposition="outside",
                cliponaxis=False,
                marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>Records: %{x:,}<extra></extra>",
            )
            chart.update_layout(coloraxis_showscale=False)
            chart.update_xaxes(title=None, rangemode="tozero")
            chart.update_yaxes(title=None)
            st.plotly_chart(style_chart(chart, height=360), use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Vendor metadata is not available for charting.")

with right:
    with st.container(border=True):
        st.markdown("**Catalog additions over time**")
        st.caption("Number of records by the month they were added to KEV.")
        dated = df.dropna(subset=["date_added"]).copy()
        if not dated.empty:
            monthly = (
                dated.assign(Month=dated["date_added"].dt.strftime("%Y-%m"))
                .groupby("Month", as_index=False)
                .size()
                .rename(columns={"size": "Records"})
                .sort_values("Month")
            )
            chart = px.area(monthly, x="Month", y="Records")
            chart.update_traces(
                line=dict(color="#2dd4bf", width=2.5),
                marker=dict(color="#60a5fa", size=5),
                fillcolor="rgba(45,212,191,.12)",
                mode="lines+markers",
                hovertemplate="<b>%{x}</b><br>Records added: %{y:,}<extra></extra>",
            )
            chart.update_xaxes(title=None, tickangle=-25, showgrid=False)
            chart.update_yaxes(title="Records added", rangemode="tozero")
            st.plotly_chart(style_chart(chart, height=360), use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No parseable date-added values are available.")

secondary_left, secondary_right = st.columns(2, gap="large")
with secondary_left:
    with st.container(border=True):
        st.markdown("**Ransomware campaign-use metadata**")
        st.caption("How records are labelled in the source catalog; this is not a prediction.")
        ransomware = df["ransomware_use"].fillna("").astype(str).str.strip()
        ransomware = ransomware.replace("", "Not specified")
        ransomware_counts = ransomware.value_counts().head(6).rename_axis("Source label").reset_index(name="Records")
        if not ransomware_counts.empty:
            chart = px.pie(
                ransomware_counts,
                names="Source label",
                values="Records",
                hole=0.68,
                color_discrete_sequence=["#2dd4bf", "#60a5fa", "#818cf8", "#fbbf24", "#f472b6", "#64748b"],
            )
            chart.update_traces(
                textposition="inside",
                textinfo="percent",
                insidetextfont=dict(color="#08111f", size=11),
                hovertemplate="<b>%{label}</b><br>Records: %{value:,}<br>Share: %{percent}<extra></extra>",
                marker=dict(line=dict(color="#111c2f", width=3)),
            )
            chart.update_layout(
                annotations=[dict(text=f"{len(df):,}<br><span style='font-size:10px'>records</span>", x=0.5, y=0.5, showarrow=False, font=dict(size=20, color="#f3f7ff"))]
            )
            st.plotly_chart(style_chart(chart, height=320, show_legend=True), use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Ransomware-use metadata is not available.")

with secondary_right:
    with st.container(border=True):
        st.markdown("**Products with the most records**")
        st.caption("Top product names by record count, as represented in the catalog.")
        if products.size:
            top_products = products.value_counts().head(8)
            product_df = top_products.rename_axis("Product").reset_index(name="Records").sort_values("Records")
            chart = px.bar(
                product_df,
                x="Records",
                y="Product",
                orientation="h",
                color_discrete_sequence=["#38bdf8"],
                text="Records",
            )
            chart.update_traces(
                textposition="outside",
                cliponaxis=False,
                marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>Records: %{x:,}<extra></extra>",
            )
            chart.update_xaxes(title=None, rangemode="tozero")
            chart.update_yaxes(title=None)
            st.plotly_chart(style_chart(chart, height=320), use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Product metadata is not available for charting.")

st.markdown("---")
st.markdown('<div class="cyber-eyebrow">03 / Latest catalog activity</div>', unsafe_allow_html=True)
latest_col, note_col = st.columns([1.65, 1], gap="large")
with latest_col:
    with st.container(border=True):
        st.markdown("**Recently added records**")
        st.caption("Latest available entries, sorted by the source date-added field.")
        recent = df.sort_values("date_added", ascending=False, na_position="last").head(8)
        display_columns = [
            column
            for column in ["cve_id", "vendor", "product", "vulnerability_name", "date_added"]
            if column in recent.columns
        ]
        st.dataframe(recent[display_columns], use_container_width=True, hide_index=True)
with note_col:
    with st.container(border=True):
        st.markdown("**Your research workflow**")
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
        st.info("Open the relevant workspace page from the sidebar to continue.")

st.caption(
    "Research note: catalog similarity is not a substitute for security assessment or expert review. "
    "CISA KEV is a vulnerability catalog, not a commercial tool rating source."
)
