# Cybersecurity Recommendation System

A Python-based research project exploring explainable, data-informed cybersecurity recommendations using public vulnerability data. The current prototype uses the CISA Known Exploited Vulnerabilities (KEV) catalog to find similar vulnerability records and suggest general defensive controls.

> **Scope note:** The current app does not rank commercial cybersecurity products. Similarity scores are not probabilities, and general controls must be validated against your environment and authoritative remediation guidance.

## Project goals

- Build a reproducible cybersecurity recommendation pipeline.
- Study preprocessing and machine-learning approaches with documented experiments.
- Evaluate recommendation quality with ranking metrics when a defensible relevance definition is available.
- Explain recommendations and link them to trustworthy source information.
- Deliver an interactive application using Streamlit.
- Avoid fabricated user ratings or experimental results.

## Technology stack

- **Development and experiments:** Python, Google Colab
- **Data processing:** Pandas, NumPy, Requests
- **Machine learning:** scikit-learn
- **Application:** Streamlit
- **Visualization:** Plotly, Matplotlib
- **Testing:** pytest

## Public data sources

- [National Vulnerability Database (NVD)](https://nvd.nist.gov/)
- [MITRE ATT&CK data and tools](https://attack.mitre.org/resources/attack-data-and-tools/)
- [CISA Known Exploited Vulnerabilities (KEV) Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- [CISA KEV JSON feed](https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json)

The app currently loads a local cleaned dataset when available; otherwise it attempts to fetch the official CISA KEV feed. Data availability depends on the local files and internet access.

## Run the Streamlit app locally

Python 3.10 or newer is recommended.

1. Clone this repository.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. From the repository root, start the app:

   ```bash
   streamlit run app/Home.py
   ```

The app includes these pages:

- **Dashboard:** catalog counts, data source, and exploratory charts.
- **Security Profile:** capture environment context and defensive priorities for the current session.
- **Recommendations:** search the KEV catalog, retrieve similar records, and inspect general defensive controls.
- **Model Evaluation:** view saved ranking metrics when an evaluation CSV exists.
- **Feedback & History:** record feedback and export it as CSV for the current session.

If the app cannot reach CISA and no local dataset is available, the dashboard will explain that data could not be loaded. The app does not create fake metrics to fill the gap.

## Google Colab research workflow

Open the notebook in `notebooks/` using Google Colab, or upload the complete project notebook to Colab. Run the notebook to download the catalog, clean and explore records, fit TF-IDF, compare retrieval approaches, calculate exploratory ranking metrics, and save artifacts.

The app can read `data/processed/cisa_kev_cleaned.csv` if you place that output in the repository's local working tree. The evaluation page can read `experiments/ranking_evaluation.csv` or accept an uploaded copy. Large datasets and generated model binaries are intentionally excluded by `.gitignore`.

## Research and evaluation principles

- Fit preprocessing transformations only on appropriate training data when conducting supervised experiments.
- Compare preprocessing variants under the same evaluation protocol.
- Do not invent model scores, user ratings, or experimental results.
- The KEV feed is a vulnerability catalog, not a security-tool directory and not a source of user ratings.
- Proxy relevance based on matching vendor/product fields is exploratory and is not human-judged recommendation quality.
- Keep source links and explainability visible.
- Treat this project as decision support; important security decisions require human review.

## Repository structure

```text
.
├── app/
│   ├── Home.py
│   ├── utils.py
│   └── pages/
├── data/                # Local data; raw/processed data is not committed
├── experiments/         # Reproducible model comparisons
├── notebooks/           # Google Colab/Jupyter notebooks
├── reports/             # Experiment summaries and figures
├── src/                 # Reusable research modules
├── tests/               # Automated tests
├── .gitignore
├── requirements.txt
└── README.md
```

## Project status

**In development.** The initial Streamlit dashboard and pages are in place. The next research phase is to build a sourced defensive-tool/control catalog and define a more rigorous relevance-review protocol before claiming tool-level recommendation performance.

## License

No license has been selected yet. Until a license is added, do not assume this repository grants permission to reuse its code.
