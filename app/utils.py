"""Shared helpers for the Streamlit cybersecurity recommendation app."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import requests
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

def _first_column(frame, candidates):
    return next((name for name in candidates if name in frame.columns), None)

def normalize_catalog(frame):
    mappings = {
        "cve_id": ["cve_id", "cveID"], "vendor": ["vendor", "vendorProject"],
        "product": ["product"], "vulnerability_name": ["vulnerability_name", "vulnerabilityName"],
        "description": ["description", "shortDescription"], "required_action": ["required_action", "requiredAction"],
        "date_added": ["date_added", "dateAdded"], "due_date": ["due_date", "dueDate"],
        "ransomware_use": ["ransomware_use", "knownRansomwareCampaignUse"], "notes": ["notes"],
    }
    out = pd.DataFrame(index=frame.index)
    for target, candidates in mappings.items():
        source = _first_column(frame, candidates)
        out[target] = frame[source] if source else ""
    for column in ["cve_id", "vendor", "product", "vulnerability_name", "description",
                   "required_action", "ransomware_use", "notes"]:
        out[column] = out[column].fillna("").astype(str).str.strip()
    for column in ["date_added", "due_date"]:
        out[column] = pd.to_datetime(out[column], errors="coerce", utc=True)
    if "text_for_model" in frame.columns:
        out["text_for_model"] = frame["text_for_model"].fillna("").astype(str)
    else:
        out["text_for_model"] = (
            out["vulnerability_name"] + " " + out["description"] + " " +
            out["vendor"] + " " + out["product"] + " " + out["required_action"]
        ).str.replace(r"\s+", " ", regex=True).str.strip()
    out = out[out["cve_id"].ne("")].drop_duplicates(subset=["cve_id"], keep="first")
    return out.reset_index(drop=True)

@st.cache_data(ttl=3600, show_spinner=False)
def load_catalog():
    """Load processed notebook data if available; otherwise fetch the official CISA feed."""
    local_csv = ROOT_DIR / "data" / "processed" / "cisa_kev_cleaned.csv"
    local_error = None
    if local_csv.exists():
        try:
            return normalize_catalog(pd.read_csv(local_csv)), f"Local file: {local_csv.relative_to(ROOT_DIR)}", None
        except Exception as exc:
            local_error = f"Local dataset could not be read: {type(exc).__name__}: {exc}"
    try:
        response = requests.get(CISA_KEV_URL, timeout=25,
            headers={"User-Agent": "CybersecurityRecommendationSystem/1.0"})
        response.raise_for_status()
        payload = response.json()
        records = payload.get("vulnerabilities", [])
        if not isinstance(records, list):
            raise ValueError("CISA feed did not contain a vulnerabilities list.")
        frame = normalize_catalog(pd.DataFrame(records))
        source = f"Live CISA KEV feed · catalog version {payload.get('catalogVersion', 'not supplied')} · released {payload.get('dateReleased', 'not supplied')}"
        return frame, source, local_error
    except Exception as exc:
        error = f"Unable to load local or live data. {local_error or ''} {type(exc).__name__}: {exc}".strip()
        return pd.DataFrame(columns=["cve_id","vendor","product","vulnerability_name","description","required_action","date_added","due_date","ransomware_use","text_for_model"]), "Data unavailable", error

@st.cache_resource(show_spinner=False)
def vectorize_texts(texts):
    """Cache TF-IDF representation for the current catalog text."""
    if not texts or not any(text.strip() for text in texts):
        texts = tuple(f"cve record {i}" for i in range(len(texts)))
    vectorizer = TfidfVectorizer(lowercase=True, stop_words="english",
        ngram_range=(1, 2), max_features=30000, min_df=1, sublinear_tf=True)
    return vectorizer, vectorizer.fit_transform(texts)

def recommend_similar(df, cve_id, top_n=5):
    """Return similar catalog records with cosine similarity and explanation."""
    if df.empty:
        return pd.DataFrame()
    matches = df.index[df["cve_id"].astype(str).eq(str(cve_id))]
    if len(matches) == 0:
        return pd.DataFrame()
    query_pos = int(matches[0])
    texts = tuple(df["text_for_model"].fillna("").astype(str).tolist())
    _, matrix = vectorize_texts(texts)
    scores = cosine_similarity(matrix[query_pos], matrix).ravel()
    scores[query_pos] = -1.0
    limit = min(max(int(top_n), 1), max(len(df) - 1, 0))
    if limit == 0:
        return pd.DataFrame()
    positions = scores.argsort()[::-1][:limit]
    result = df.iloc[positions][["cve_id","vendor","product","vulnerability_name","description","required_action","date_added"]].copy()
    result["similarity_score"] = scores[positions]
    result["explanation"] = "Ranked by TF-IDF cosine similarity across available catalog text and metadata."
    return result.reset_index(drop=True)

def defensive_controls(record):
    """Create general defensive guidance, not product endorsements."""
    get = record.get
    action = str(get("required_action", "") or "").strip()
    vendor = str(get("vendor", "") or "").strip()
    product = str(get("product", "") or "").strip()
    evidence = action or "Review the original CISA KEV record for applicable remediation guidance."
    return [
        {"Control":"Patch and vulnerability management",
         "Why it may help":"Validate exposure and prioritize remediation because this vulnerability appears in CISA KEV.",
         "Evidence from catalog":evidence},
        {"Control":"Asset inventory and exposure review",
         "Why it may help":"Confirm whether the affected product exists in your environment and whether it is exposed.",
         "Evidence from catalog":"Affected vendor/product: " + " / ".join(x for x in [vendor,product] if x) if vendor or product else "Vendor/product details are not available in this record."},
        {"Control":"Remediation verification",
         "Why it may help":"Track the fix or mitigation and verify completion rather than relying only on ticket status.",
         "Evidence from catalog":evidence},
        {"Control":"Monitoring and incident readiness",
         "Why it may help":"Review relevant logs, alerts, and response procedures for affected assets.",
         "Evidence from catalog":"General defensive guidance; validate against local telemetry and risk."},
    ]
