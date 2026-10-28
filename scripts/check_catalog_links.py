"""Check whether curated catalog URLs respond over HTTPS.

Run manually from the repository root:
    python scripts/check_catalog_links.py

Some official sites block automated requests or rate-limit clients. A reported
failure should be verified in a browser before removing a source URL.
"""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
CATALOGS = [
    (ROOT / "data" / "tool_catalog.csv", ["official_url", "source_url"]),
    (ROOT / "data" / "control_catalog.csv", ["official_source"]),
]
HEADERS = {"User-Agent": "CybersecurityRecommendationSystem-source-check/1.0"}


def main() -> int:
    urls: list[tuple[str, str]] = []
    failed = False
    for path, columns in CATALOGS:
        frame = pd.read_csv(path, keep_default_na=False)
        for column in columns:
            if column not in frame.columns:
                print(f"ERROR {path.relative_to(ROOT)}: missing column {column}")
                return 1
            for row_number, value in enumerate(frame[column], start=2):
                url = str(value).strip()
                label = f"{path.relative_to(ROOT)}:{row_number}:{column}"
                if not url.startswith("https://"):
                    print(f"FAIL {label} {url!r} (expected HTTPS URL)")
                    failed = True
                    continue
                urls.append((label, url))

    with requests.Session() as session:
        session.headers.update(HEADERS)
        for label, url in urls:
            try:
                response = session.get(url, timeout=15, allow_redirects=True, stream=True)
                status = response.status_code
                final_url = response.url
                response.close()
                if status >= 400:
                    failed = True
                    print(f"FAIL {label} HTTP {status} {final_url}")
                else:
                    print(f"OK   {label} HTTP {status} {final_url}")
            except requests.RequestException as exc:
                failed = True
                print(f"FAIL {label} {type(exc).__name__}: {exc}")

    print(f"Checked {len(urls)} URLs; {'some checks failed' if failed else 'all responded successfully'}.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
