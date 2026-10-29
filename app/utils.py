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


def apply_app_theme():
    """Apply the shared, accessible visual theme across every Streamlit page."""
    st.markdown(
        """
        <style>
        :root {
            --cyber-bg: #0b1220;
            --cyber-panel: #111c2f;
            --cyber-panel-soft: #15233a;
            --cyber-border: rgba(148, 163, 184, 0.18);
            --cyber-text: #e7eef8;
            --cyber-muted: #9fb0c7;
            --cyber-teal: #2dd4bf;
            --cyber-blue: #60a5fa;
        }
        .stApp {
            background:
                radial-gradient(ellipse at 12% 0%, rgba(45, 212, 191, 0.08), transparent 34%),
                radial-gradient(ellipse at 92% 4%, rgba(96, 165, 250, 0.09), transparent 30%),
                var(--cyber-bg);
            color: var(--cyber-text);
        }
        [data-testid="stHeader"] { background: rgba(11, 18, 32, 0.82); }
        [data-testid="stSidebar"] {
            background: #080f1c;
            border-right: 1px solid var(--cyber-border);
        }
        [data-testid="stSidebar"] * { color: var(--cyber-text); }
        .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1440px; }
        h1, h2, h3 { color: #f3f7ff !important; letter-spacing: -0.025em; }
        h1 { font-weight: 760 !important; }
        p, li, label, .stCaption, [data-testid="stMarkdownContainer"] { color: var(--cyber-text); }
        [data-testid="stCaptionContainer"], small { color: var(--cyber-muted) !important; }
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(21,35,58,.96), rgba(15,27,45,.96));
            border: 1px solid var(--cyber-border);
            border-radius: 16px;
            padding: 18px 20px;
            box-shadow: 0 10px 28px rgba(0,0,0,.12);
        }
        [data-testid="stMetricLabel"] { color: var(--cyber-muted) !important; }
        [data-testid="stMetricValue"] { color: #f3f7ff !important; font-weight: 750; }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--cyber-border) !important;
            border-radius: 16px !important;
            background: rgba(17, 28, 47, 0.62);
        }
        div[data-baseweb="tab-list"] { gap: 8px; }
        button[data-baseweb="tab"] {
            border-radius: 10px 10px 0 0;
            padding: 10px 16px;
        }
        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
            border-radius: 10px;
            border: 1px solid rgba(45,212,191,.42);
            font-weight: 650;
            transition: all .16s ease;
        }
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
            background: linear-gradient(135deg, #0f9f91, #0d9488);
            color: #ffffff;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            border-color: var(--cyber-teal);
            transform: translateY(-1px);
        }
        input, textarea, [data-baseweb="select"] > div {
            border-radius: 10px !important;
        }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            border: 1px solid var(--cyber-border);
            border-radius: 12px;
            overflow: hidden;
        }
        [data-testid="stAlert"] { border-radius: 12px; }
        hr { border-color: var(--cyber-border); }
        a { color: var(--cyber-teal) !important; }
        .cyber-eyebrow {
            color: var(--cyber-teal);
            font-size: .78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .16em;
            margin-bottom: .5rem;
        }
        .cyber-hero {
            background: linear-gradient(120deg, rgba(17,28,47,.97), rgba(18,43,62,.92));
            border: 1px solid rgba(45,212,191,.24);
            border-radius: 22px;
            padding: 30px 32px;
            margin: 8px 0 24px 0;
            box-shadow: 0 18px 50px rgba(0,0,0,.18);
        }
        .cyber-hero h1 { margin: 0 0 12px 0; font-size: clamp(2rem, 4vw, 3.25rem); }
        .cyber-hero p { color: #b9c8db; max-width: 760px; line-height: 1.7; margin-bottom: 0; }
        .cyber-chip {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(45,212,191,.10);
            border: 1px solid rgba(45,212,191,.25);
            color: #80f1df;
            font-size: .76rem;
            font-weight: 700;
            margin-bottom: 14px;
        }
        @media (max-width: 700px) {
            .block-container { padding-top: 1rem; }
            .cyber-hero { padding: 22px; border-radius: 16px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        """
        <div style="padding: 10px 4px 18px 4px; margin-bottom: 12px; border-bottom: 1px solid rgba(148,163,184,.18);">
          <div style="display:flex; align-items:center; gap:10px;">
            <div style="background:linear-gradient(135deg,#0f9f91,#164e63); width:42px; height:42px; border-radius:13px; display:flex; align-items:center; justify-content:center; font-size:23px;">🛡️</div>
            <div>
              <div style="font-size:14px; font-weight:800; letter-spacing:.02em; color:#f3f7ff;">CYBER INTELLIGENCE</div>
              <div style="font-size:11px; color:#9fb0c7; margin-top:3px;">DEFENSIVE RESEARCH WORKSPACE</div>
            </div>
          </div>
          <div style="margin-top:14px; display:inline-block; padding:5px 9px; border-radius:999px; border:1px solid rgba(45,212,191,.24); background:rgba(45,212,191,.08); color:#80f1df; font-size:10px; font-weight:700; letter-spacing:.08em;">● RESEARCH PROTOTYPE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

