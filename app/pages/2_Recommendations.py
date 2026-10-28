from pathlib import Path
import sys
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))
from utils import load_catalog, recommend_similar, defensive_controls

st.set_page_config(page_title="Recommendations", page_icon="🔎", layout="wide")
st.title("🔎 Recommendations")
st.write("Find similar entries in the CISA KEV catalog and review general defensive controls.")
df, source_label, load_error = load_catalog()
if load_error:
    st.warning(load_error)
if df.empty:
    st.error("The vulnerability catalog is unavailable. Check the dashboard or try again later.")
    st.stop()

st.caption(f"Source: {source_label}")
st.warning("These are catalog-similarity results and general defensive suggestions, not a ranking of security vendors or proof that a specific product is suitable for your environment.")

search_text = st.text_input("Search CVE, vendor, product, or description")
filtered = df.copy()
if search_text.strip():
    needle = search_text.strip().casefold()
    searchable = (filtered["cve_id"].astype(str) + " " + filtered["vendor"].astype(str) + " " +
        filtered["product"].astype(str) + " " + filtered["vulnerability_name"].astype(str) + " " +
        filtered["description"].astype(str)).str.casefold()
    filtered = filtered.loc[searchable.str.contains(needle, regex=False, na=False)]
if filtered.empty:
    st.info("No records match that search. Try a CVE identifier, vendor, or shorter keyword.")
    st.stop()

labels = filtered["cve_id"].astype(str) + " — " + filtered["vendor"].astype(str) + " / " + filtered["product"].astype(str)
label_to_id = dict(zip(labels, filtered["cve_id"].astype(str)))
selected_label = st.selectbox("Choose a vulnerability record", labels.tolist())
selected_id = label_to_id[selected_label]
top_n = st.slider("Number of similar records", min_value=3, max_value=10, value=5)
selected_rows = df[df["cve_id"].astype(str).eq(selected_id)]

if not selected_rows.empty:
    record = selected_rows.iloc[0]
    st.subheader(f"Selected record: {selected_id}")
    st.write("**Vendor / product:**", " / ".join(x for x in [record["vendor"], record["product"]] if x) or "Not supplied")
    if record["vulnerability_name"]:
        st.write("**Vulnerability:**", record["vulnerability_name"])
    if record["description"]:
        st.write("**Description:**", record["description"])
    if record["required_action"]:
        st.write("**CISA required action:**", record["required_action"])
    else:
        st.info("The selected record does not include a required-action field in the available data.")

    st.subheader("Similar vulnerability records")
    try:
        recommendations = recommend_similar(df, selected_id, top_n=top_n)
        if recommendations.empty:
            st.info("There are not enough records to calculate similar results.")
        else:
            recommendations["similarity_score"] = recommendations["similarity_score"].round(4)
            st.dataframe(recommendations, use_container_width=True, hide_index=True)
            st.caption("Similarity scores are not probabilities.")
            st.download_button("Download these recommendations as CSV",
                data=recommendations.to_csv(index=False).encode("utf-8"),
                file_name=f"similar_vulnerabilities_{selected_id}.csv", mime="text/csv")
    except Exception as exc:
        st.error(f"Could not calculate recommendations: {type(exc).__name__}: {exc}")

    st.subheader("General defensive controls to consider")
    st.dataframe(pd.DataFrame(defensive_controls(record.to_dict())), use_container_width=True, hide_index=True)
    st.caption("Validate every suggestion against your assets, policies, and authoritative remediation guidance.")
