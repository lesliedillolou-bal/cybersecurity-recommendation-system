from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))
st.set_page_config(page_title="Model Evaluation", page_icon="📊", layout="wide")
st.title("📊 Model Evaluation")
st.write("Review experimental results produced by the Colab notebook.")
st.caption("This page does not invent metrics. It displays saved evaluation files when available.")

default_path = ROOT_DIR / "experiments" / "ranking_evaluation.csv"
uploaded = st.file_uploader("Optionally upload ranking_evaluation.csv", type=["csv"])
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
    st.info("No evaluation results are available yet. Run the Colab notebook through the evaluation section, then place experiments/ranking_evaluation.csv in the repository or upload it above.")
    st.markdown("Planned ranking metrics: Precision@5, Recall@5, MAP@5, NDCG@5, and runtime. The notebook uses documented proxy relevance labels based on catalog vendor/product fields; these are exploratory results, not human-judged recommendation quality.")
    st.stop()

st.success(f"Loaded evaluation results from: {source}")
st.dataframe(results, use_container_width=True, hide_index=True)
metric_columns = [c for c in ["precision_at_5","recall_at_5","map_at_5","ndcg_at_5"] if c in results.columns]
if metric_columns and "method" in results.columns:
    long_form = results.melt(id_vars=["method"], value_vars=metric_columns, var_name="Metric", value_name="Score")
    st.plotly_chart(px.bar(long_form, x="Metric", y="Score", color="method", barmode="group", title="Ranking metrics by retrieval method"), use_container_width=True)
if "runtime_seconds" in results.columns and "method" in results.columns:
    st.plotly_chart(px.bar(results, x="method", y="runtime_seconds", title="Evaluation runtime (seconds)"), use_container_width=True)

st.subheader("How to interpret these results")
st.markdown("- **Precision@5:** fraction of the five returned records marked relevant by the documented proxy.\n- **Recall@5:** fraction of all proxy-relevant records retrieved in the top five.\n- **MAP@5:** average precision over the ranked top-five results.\n- **NDCG@5:** ranking quality with higher ranks weighted more strongly.\n- **Runtime:** measured evaluation loop time for the recorded run.\n\nThe catalog does not contain user ratings or expert relevance judgments. Treat these metrics as proxy-based exploratory comparisons, and do not claim production effectiveness from them alone.")
