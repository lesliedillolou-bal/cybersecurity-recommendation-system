from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
URL_PREFIX = "https://"


def test_tool_catalog_has_required_fields_unique_names_and_https_sources():
    catalog = pd.read_csv(ROOT / "data" / "tool_catalog.csv", keep_default_na=False)
    required = {
        "name", "category", "description", "strengths", "limitations",
        "cost_model", "deployment", "suitable_environments", "priorities",
        "skill_level", "official_url", "source_url", "last_reviewed",
    }
    assert required.issubset(catalog.columns)
    assert not catalog.empty
    assert catalog["name"].str.strip().ne("").all()
    assert catalog["name"].is_unique
    assert catalog["official_url"].str.startswith(URL_PREFIX).all()
    assert catalog["source_url"].str.startswith(URL_PREFIX).all()


def test_control_catalog_has_required_fields_unique_ids_and_https_sources():
    catalog = pd.read_csv(ROOT / "data" / "control_catalog.csv", keep_default_na=False)
    required = {
        "control_id", "control_name", "category", "description", "why_it_matters",
        "priority_tags", "environment_tags", "effort", "official_source",
        "source_name", "last_reviewed",
    }
    assert required.issubset(catalog.columns)
    assert not catalog.empty
    assert catalog["control_id"].is_unique
    assert catalog["control_name"].str.strip().ne("").all()
    assert catalog["official_source"].str.startswith(URL_PREFIX).all()
