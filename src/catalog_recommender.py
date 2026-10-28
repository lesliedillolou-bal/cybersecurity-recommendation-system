"""Explainable matching for a curated defensive tool and control catalog."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT_DIR / "data" / "tool_catalog.csv"
CONTROLS_PATH = ROOT_DIR / "data" / "control_catalog.csv"


def load_tool_catalog() -> pd.DataFrame:
    """Load the reviewed starter catalog shipped with the repository."""
    return pd.read_csv(TOOLS_PATH, keep_default_na=False)


def load_control_catalog() -> pd.DataFrame:
    """Load the defensive control starter catalog shipped with the repository."""
    return pd.read_csv(CONTROLS_PATH, keep_default_na=False)


def _tokens(value) -> set[str]:
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip() for item in value if str(item).strip()}
    return {part.strip() for part in str(value or "").split(";") if part.strip()}


def recommend_tools(catalog: pd.DataFrame, profile: dict | None = None) -> pd.DataFrame:
    """Score tools by transparent profile-tag overlap; never imply a security guarantee."""
    profile = profile or {}
    priorities = _tokens(profile.get("priorities", []))
    environment = str(profile.get("environment", "")).strip()
    constraints = _tokens(profile.get("constraints", []))
    maturity = str(profile.get("maturity", "")).strip()

    rows = []
    for _, row in catalog.iterrows():
        tool_environments = _tokens(row.get("suitable_environments", ""))
        tool_priorities = _tokens(row.get("priorities", ""))
        score = 0
        reasons = []
        matched_priorities = sorted(priorities & tool_priorities)
        if matched_priorities:
            score += 3 * len(matched_priorities)
            reasons.append("Matches priorities: " + ", ".join(matched_priorities))
        if environment and (environment in tool_environments or environment == "Not sure yet"):
            score += 2
            if environment != "Not sure yet":
                reasons.append(f"Environment match: {environment}")
        if "Prefer open-source tools" in constraints and "Open-source" in str(row.get("cost_model", "")):
            score += 2
            reasons.append("Open-source option")
        if "Limited budget" in constraints and ("Open-source" in str(row.get("cost_model", "")) or "Community edition" in str(row.get("cost_model", ""))):
            score += 1
            reasons.append("Has an open-source/community option; deployment still has costs")
        if "Need simple deployment" in constraints:
            level = str(row.get("skill_level", ""))
            if "Beginner" in level:
                score += 2
                reasons.append("Catalog labels this tool beginner-friendly")
            elif "Advanced" in level:
                score -= 1
                reasons.append("May require more operational expertise")
        if maturity == "Learning / starting" and "Beginner" in str(row.get("skill_level", "")):
            score += 1
            if "Catalog labels this tool beginner-friendly" not in reasons:
                reasons.append("May be approachable for a learning-stage team")
        rows.append({
            **row.to_dict(),
            "match_score": score,
            "match_reasons": "; ".join(reasons) if reasons else "No strong profile-tag match; review the tool description manually.",
        })
    if not rows:
        return pd.DataFrame(columns=list(catalog.columns) + ["match_score", "match_reasons"])
    result = pd.DataFrame(rows)
    return result.sort_values(["match_score", "name"], ascending=[False, True]).reset_index(drop=True)


def recommend_controls(catalog: pd.DataFrame, profile: dict | None = None) -> pd.DataFrame:
    """Prioritize controls by profile priority and environment tags."""
    profile = profile or {}
    priorities = _tokens(profile.get("priorities", []))
    environment = str(profile.get("environment", "")).strip()
    rows = []
    for _, row in catalog.iterrows():
        control_priorities = _tokens(row.get("priority_tags", ""))
        environments = _tokens(row.get("environment_tags", ""))
        matched = sorted(priorities & control_priorities)
        score = 3 * len(matched)
        reasons = []
        if matched:
            reasons.append("Matches priorities: " + ", ".join(matched))
        if environment and (environment in environments or environment == "Not sure yet"):
            score += 2
            if environment != "Not sure yet":
                reasons.append(f"Applicable environment: {environment}")
        rows.append({
            **row.to_dict(),
            "match_score": score,
            "match_reasons": "; ".join(reasons) if reasons else "Foundational control; review applicability for your environment.",
        })
    if not rows:
        return pd.DataFrame(columns=list(catalog.columns) + ["match_score", "match_reasons"])
    return pd.DataFrame(rows).sort_values(
        ["match_score", "control_name"], ascending=[False, True]
    ).reset_index(drop=True)
