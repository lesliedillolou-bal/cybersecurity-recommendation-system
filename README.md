# Cybersecurity Recommendation System

A Python-based research project exploring machine-learning and recommendation techniques for suggesting relevant cybersecurity tools, defensive controls, and learning resources from public cybersecurity data.

## Project goals

- Build a reproducible cybersecurity recommendation pipeline.
- Study five preprocessing techniques and measure their effects.
- Compare recommendation and machine-learning algorithms using consistent experiments.
- Evaluate recommendation quality with ranking metrics such as Precision@5, Recall@5, MAP@5, and NDCG@5 where the dataset and relevance labels support them.
- Explain recommendations and link them to trustworthy source information.
- Deliver an interactive application using Streamlit.

## Technology stack

- **Development and experiments:** Python, Google Colab
- **Data processing:** Pandas, NumPy, Requests
- **Machine learning:** scikit-learn
- **Application:** Streamlit
- **Visualization:** Plotly, Matplotlib
- **Testing:** pytest

## Planned data sources

- [National Vulnerability Database (NVD)](https://nvd.nist.gov/)
- [MITRE ATT&CK data and tools](https://attack.mitre.org/resources/attack-data-and-tools/)
- [CISA Known Exploited Vulnerabilities (KEV) Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)

Data-source terms and API requirements will be reviewed before ingestion. These sources do not inherently provide user ratings for recommendations, so relevance labels and evaluation assumptions will be documented rather than presented as real user behavior.

## Planned repository structure

```text
.
├── app/                 # Streamlit application
├── data/                # Local data; raw data is not committed
├── experiments/         # Reproducible model comparisons
├── notebooks/           # Google Colab/Jupyter notebooks
├── reports/             # Experiment summaries and figures
├── src/                 # Reusable Python modules
├── tests/               # Automated tests
├── .gitignore
├── requirements.txt
└── README.md
```

## Getting started

Python 3.10 or newer is recommended.

1. Clone this repository.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. The application and data pipeline will be added incrementally as the project develops.

To use Google Colab, open a notebook from the `notebooks/` directory in Colab or upload it to your Google Drive.

## Research and evaluation principles

- Split data before fitting transformations to prevent data leakage.
- Compare preprocessing variants under the same evaluation protocol.
- Do not invent model scores, user ratings, or experimental results.
- Report limitations and use source-linked explanations for recommendations.
- Treat this project as decision support; important security decisions require human review.

## Project status

**In development.** Dataset preparation, baseline models, evaluation, and the Streamlit interface are planned next.

## License

No license has been selected yet. Until a license is added, do not assume this repository grants permission to reuse its code.
