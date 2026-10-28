from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(ROOT_DIR))
from src.evaluation import evaluate_judged_rankings

st.set_page_config(page_title="Model Evaluation", page_icon="📊", layout="wide")
st.title("📊 Model Evaluation")
st.write("Review saved experiments or evaluate ranked recommendations against explicit relevance judgments.")
st.caption("This page does not invent metrics. Profile-match scores are not ground truth and are never used as relevance labels.")

st.subheader("Saved exploratory evaluation")
default_path = ROOT_DIR / "experiments" / "ranking_evaluation.csv"
uploaded = st.file_uploader("Optionally upload ranking_evaluation.csv", type=["csv"], key="saved_metrics")
results, source = None, None
if uploaded is not None:
    try:
        results, source = pd.read_csv(uploaded), "Uploaded file"
    except Exception as exc:
        st.error(f"Could not read uploaded CSV: {type(exc).__name__}: {exc}")
elif default_path.exists():
    try:
        results, source = pd.read_csv(default_path), str(default_path.relative_to(ROOT_DIR))
    except Exception as exc:
        st.error(f"Could not read saved results: {type(exc).__name__}: {exc}")

if results is None:
    st.info("No precomputed evaluation results are available. Run the Colab notebook through its evaluation section, then upload ranking_evaluation.csv.")
else:
    st.success(f"Loaded evaluation results from: {source}")
    st.dataframe(results, use_container_width=True, hide_index=True)
    metric_columns = [c for c in ["precision_at_5", "recall_at_5", "map_at_5", "ndcg_at_5"] if c in results.columns]
    if metric_columns and "method" in results.columns:
        long_form = results.melt(id_vars=["method"], value_vars=metric_columns, var_name="Metric", value_name="Score")
        st.plotly_chart(
            px.bar(long_form, x="Metric", y="Score", color="method", barmode="group", title="Ranking metrics by retrieval method"),
            use_container_width=True,
        )
    if "runtime_seconds" in results.columns and "method" in results.columns:
        st.plotly_chart(px.bar(results, x="method", y="runtime_seconds", title="Evaluation runtime (seconds)"), use_container_width=True)
    st.caption(
        "The existing notebook's vendor/product proxy labels are exploratory, not human-judged relevance. "
        "Do not interpret them as evidence of production effectiveness."
    )

st.divider()
st.subheader("Evaluate with explicit relevance judgments")
st.write(
    "Upload two CSV files: a ranked-results file with columns `method,item_id,rank`, "
    "and a separate judgment file with columns `item_id,relevance`. Relevance must be a non-negative grade "
    "(0 means not relevant; values above 0 mean relevant). Use judgments made under a documented review protocol."
)
rankings_upload = st.file_uploader("Ranked recommendations CSV", type=["csv"], key="judged_rankings")
judgments_upload = st.file_uploader("Human relevance judgments CSV", type=["csv"], key="human_judgments")
k = st.slider("Evaluate top K results", min_value=1, max_value=20, value=5, key="judged_k")

if rankings_upload is not None and judgments_upload is not None:
    try:
        rankings_frame = pd.read_csv(rankings_upload)
        judgments_frame = pd.read_csv(judgments_upload)
        judged_results = evaluate_judged_rankings(rankings_frame, judgments_frame, k=k)
        if judged_results.empty:
            st.info("No ranking rows or relevance judgments were provided.")
        else:
            st.dataframe(judged_results.round(4), use_container_width=True, hide_index=True)
            st.download_button(
                "Download judged evaluation metrics",
                data=judged_results.to_csv(index=False).encode("utf-8"),
                file_name=f"human_judged_ranking_metrics_at_{k}.csv",
                mime="text/csv",
            )
    except Exception as exc:
        st.error(f"Could not evaluate these files: {type(exc).__name__}: {exc}")
else:
    st.info("Upload both files to calculate metrics. The app will not infer relevance from match scores or usefulness ratings.")

st.subheader("Metric definitions")
st.markdown(
    "- **Precision@K:** fraction of the top K returned items judged relevant. The denominator is K.\n"
    "- **Recall@K:** fraction of all judged-relevant items returned in the top K.\n"
    "- **MAP@K:** average precision over relevant hits in the top K.\n"
    "- **NDCG@K:** ranking quality with graded relevance and higher ranks weighted more strongly.\n\n"
    "If no items are marked relevant, recall, MAP, or NDCG may be undefined. A relevance judgment set should be created "
    "independently of the recommender scores and held separate from development data when used for research claims."
)
