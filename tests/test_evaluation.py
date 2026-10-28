import pandas as pd
import pytest

from src.evaluation import evaluate_judged_rankings


def test_evaluation_uses_explicit_judgments_not_match_scores():
    rankings = pd.DataFrame([
        {"method": "A", "item_id": "x", "rank": 1, "match_score": 99},
        {"method": "A", "item_id": "y", "rank": 2, "match_score": 1},
        {"method": "A", "item_id": "z", "rank": 3, "match_score": 0},
        {"method": "B", "item_id": "z", "rank": 1, "match_score": 0},
        {"method": "B", "item_id": "y", "rank": 2, "match_score": 1},
        {"method": "B", "item_id": "x", "rank": 3, "match_score": 99},
    ])
    judgments = pd.DataFrame([
        {"item_id": "x", "relevance": 0},
        {"item_id": "y", "relevance": 1},
        {"item_id": "z", "relevance": 1},
    ])

    result = evaluate_judged_rankings(rankings, judgments, k=2).set_index("method")
    assert result.loc["A", "precision_at_2"] == 0.5
    assert result.loc["B", "precision_at_2"] == 1.0
    assert result.loc["B", "ndcg_at_2"] > result.loc["A", "ndcg_at_2"]


def test_evaluation_rejects_duplicate_judgments():
    rankings = pd.DataFrame([{"method": "A", "item_id": "x", "rank": 1}])
    judgments = pd.DataFrame([
        {"item_id": "x", "relevance": 1},
        {"item_id": "x", "relevance": 0},
    ])
    with pytest.raises(ValueError, match="one row per item_id"):
        evaluate_judged_rankings(rankings, judgments)



def test_evaluation_requires_judgment_for_every_ranked_item():
    rankings = pd.DataFrame([
        {"method": "A", "item_id": "x", "rank": 1},
        {"method": "A", "item_id": "y", "rank": 2},
    ])
    judgments = pd.DataFrame([{"item_id": "x", "relevance": 1}])
    with pytest.raises(ValueError, match="every ranked item"):
        evaluate_judged_rankings(rankings, judgments)
