from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
from utils import load_catalog

st.set_page_config(page_title="Cybersecurity Recommendation System", page_icon="🛡️", layout="wide")
st.title("🛡️ Cybersecurity Recommendation System")
st.caption("An explainable, data-informed defensive decision-support research prototype.")

df, source_label, load_error = load_catalog()
st.info("This prototype currently uses the CISA Known Exploited Vulnerabilities (KEV) catalog. It can surface similar vulnerability records and general defensive controls; it does not yet rank commercial security products.")
if load_error:
    st.warning(load_error)
if df.empty:
    st.error("No catalog records are available right now. Check the connection and refresh the page.")
    st.markdown("You can still explore the app pages, but live recommendations require the cleaned dataset from the Colab notebook or access to the official CISA feed.")
    st.stop()

st.caption(f"Data source: {source_label}")
cols = st.columns(4)
cols[0].metric("Catalog records", f"{len(df):,}")
cols[1].metric("Unique vendors", f"{df['vendor'].replace('', pd.NA).nunique():,}")
cols[2].metric("Unique products", f"{df['product'].replace('', pd.NA).nunique():,}")
cols[3].metric("Records with required action", f"{int(df['required_action'].astype(str).str.strip().ne('').sum()):,}")

left, right = st.columns(2)
with left:
    if df["vendor"].astype(str).str.strip().ne("").any():
        top = df.loc[df["vendor"].astype(str).str.strip().ne(""), "vendor"].value_counts().head(12)
        plot_df = top.rename_axis("vendor").reset_index(name="records").sort_values("records")
        st.plotly_chart(px.bar(plot_df, x="records", y="vendor", orientation="h", title="Vendors appearing most often in KEV"), use_container_width=True)
    else:
        st.info("Vendor metadata is not available for charting.")
with right:
    if df["date_added"].notna().any():
        monthly = df.dropna(subset=["date_added"]).assign(month=lambda x: x["date_added"].dt.strftime("%Y-%m")).groupby("month", as_index=False).size().rename(columns={"size":"records"})
        st.plotly_chart(px.line(monthly, x="month", y="records", markers=True, title="KEV records by month added"), use_container_width=True)
    else:
        st.info("No parseable date-added values are available.")

st.subheader("Recently added catalog records")
recent = df.sort_values("date_added", ascending=False, na_position="last").head(10)
columns = [c for c in ["cve_id","vendor","product","vulnerability_name","date_added"] if c in recent.columns]
st.dataframe(recent[columns], use_container_width=True, hide_index=True)
st.subheader("Navigate the app")
a, b, c = st.columns(3)
a.markdown("**Security Profile**\n\nDescribe your environment and priorities.")
b.markdown("**Recommendations**\n\nExplore similar vulnerability records and defensive controls.")
c.markdown("**Model Evaluation**\n\nReview saved experimental metrics when available.")
st.caption("Research note: catalog similarity is not a substitute for a security assessment or expert review.")
