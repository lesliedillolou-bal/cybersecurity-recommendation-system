import pandas as pd

from src.catalog_recommender import recommend_controls, recommend_tools


def test_tool_recommender_explains_priority_match():
    catalog = pd.DataFrame([{
        "name": "Example Monitor",
        "category": "Monitoring",
        "description": "Example defensive monitor",
        "strengths": "Logs",
        "limitations": "Needs tuning",
        "cost_model": "Open-source",
        "deployment": "Self-managed",
        "suitable_environments": "Cloud;Hybrid",
        "priorities": "Security monitoring;Cloud security",
        "skill_level": "Intermediate",
        "official_url": "https://example.org/",
        "source_url": "https://example.org/docs",
        "last_reviewed": "2026-10-28",
    }])
    profile = {
        "environment": "Cloud",
        "priorities": ["Security monitoring"],
        "constraints": ["Prefer open-source tools"],
        "maturity": "Developing",
    }
    result = recommend_tools(catalog, profile)
    assert result.loc[0, "match_score"] == 7
    assert "Security monitoring" in result.loc[0, "match_reasons"]
    assert "Open-source option" in result.loc[0, "match_reasons"]


def test_control_recommender_returns_ranked_controls():
    catalog = pd.DataFrame([{
        "control_id": "C1",
        "control_name": "Vulnerability management",
        "category": "Protection",
        "description": "Documented control",
        "why_it_matters": "Reason",
        "priority_tags": "Vulnerability management",
        "environment_tags": "Cloud;Hybrid",
        "effort": "Medium",
        "official_source": "https://example.org/",
        "source_name": "Example",
        "last_reviewed": "2026-10-28",
    }])
    result = recommend_controls(catalog, {
        "environment": "Cloud",
        "priorities": ["Vulnerability management"],
    })
    assert result.loc[0, "match_score"] == 5
    assert "Vulnerability management" in result.loc[0, "match_reasons"]
