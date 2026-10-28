"""Ranking metrics based only on explicit relevance judgments, not profile-match scores."""
from __future__ import annotations

import math
import pandas as pd


def evaluate_judged_rankings(
    rankings: pd.DataFrame,
    judgments: pd.DataFrame,
    k: int = 5,
) -> pd.DataFrame:
    """Evaluate ranked items against a separate human-judgment table.

    rankings must contain method, item_id, rank. judgments must contain
    item_id, relevance where relevance is a non-negative numeric grade.
    Relevance is binarized (>0) for precision, recall, and average precision;
    graded values are used for NDCG.
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    required_rank = {"method", "item_id", "rank"}
    required_judgment = {"item_id", "relevance"}
    if not required_rank.issubset(rankings.columns):
        raise ValueError(f"rankings must include columns: {sorted(required_rank)}")
    if not required_judgment.issubset(judgments.columns):
        raise ValueError(f"judgments must include columns: {sorted(required_judgment)}")
    if rankings.empty or judgments.empty:
        return pd.DataFrame(columns=["method", f"precision_at_{k}", f"recall_at_{k}", f"map_at_{k}", f"ndcg_at_{k}"])

    rank_data = rankings.copy()
    judgment_data = judgments.copy()
    rank_data["rank"] = pd.to_numeric(rank_data["rank"], errors="raise")
    judgment_data["relevance"] = pd.to_numeric(judgment_data["relevance"], errors="raise")
    if (rank_data["rank"] < 1).any():
        raise ValueError("rank values must be 1 or greater")
    if (judgment_data["relevance"] < 0).any():
        raise ValueError("relevance values must be non-negative")
    if judgment_data["item_id"].duplicated().any():
        raise ValueError("judgments must have one row per item_id")
    relevance_map = dict(zip(judgment_data["item_id"].astype(str), judgment_data["relevance"].astype(float)))
    relevant_total = sum(value > 0 for value in relevance_map.values())
    output = []

    for method, group in rank_data.groupby("method", sort=True):
        group = group.sort_values("rank").drop_duplicates("item_id").head(k)
        grades = [relevance_map.get(str(item_id), 0.0) for item_id in group["item_id"]]
        binary = [grade > 0 for grade in grades]
        precision = sum(binary) / k
        recall = sum(binary) / relevant_total if relevant_total else math.nan
        precision_at_i = []
        hits = 0
        for index, is_relevant in enumerate(binary, start=1):
            if is_relevant:
                hits += 1
                precision_at_i.append(hits / index)
        average_precision = (
            sum(precision_at_i) / min(relevant_total, k)
            if relevant_total else math.nan
        )
        dcg = sum((2 ** grade - 1) / math.log2(index + 1) for index, grade in enumerate(grades, start=1))
        ideal_grades = sorted(relevance_map.values(), reverse=True)[:k]
        idcg = sum((2 ** grade - 1) / math.log2(index + 1) for index, grade in enumerate(ideal_grades, start=1))
        ndcg = dcg / idcg if idcg else math.nan
        output.append({
            "method": str(method),
            f"precision_at_{k}": precision,
            f"recall_at_{k}": recall,
            f"map_at_{k}": average_precision,
            f"ndcg_at_{k}": ndcg,
        })
    return pd.DataFrame(output)
