import pandas as pd

from app.utils import defensive_controls, normalize_catalog, recommend_similar


def test_normalize_catalog_maps_cisa_field_names():
    raw = pd.DataFrame([{
        "cveID": "CVE-2025-1234",
        "vendorProject": "Example Vendor",
        "product": "Example Product",
        "vulnerabilityName": "Example issue",
        "shortDescription": "A sample vulnerability",
        "requiredAction": "Apply the vendor update",
        "dateAdded": "2025-01-10",
    }])

    result = normalize_catalog(raw)

    assert len(result) == 1
    assert result.loc[0, "cve_id"] == "CVE-2025-1234"
    assert result.loc[0, "vendor"] == "Example Vendor"
    assert "Example issue" in result.loc[0, "text_for_model"]


def test_recommend_similar_excludes_query_record():
    frame = pd.DataFrame([
        {
            "cve_id": "CVE-2025-0001", "vendor": "Example", "product": "Browser",
            "vulnerability_name": "Browser memory vulnerability",
            "description": "Memory access issue in browser component",
            "required_action": "Apply security update", "date_added": pd.NaT,
            "due_date": pd.NaT, "ransomware_use": "", "notes": "",
            "text_for_model": "browser memory vulnerability security update",
        },
        {
            "cve_id": "CVE-2025-0002", "vendor": "Example", "product": "Browser",
            "vulnerability_name": "Browser input validation issue",
            "description": "Input validation weakness in browser component",
            "required_action": "Apply security update", "date_added": pd.NaT,
            "due_date": pd.NaT, "ransomware_use": "", "notes": "",
            "text_for_model": "browser input validation vulnerability security update",
        },
    ])

    result = recommend_similar(frame, "CVE-2025-0001", top_n=1)

    assert len(result) == 1
    assert result.loc[0, "cve_id"] == "CVE-2025-0002"
    assert 0 <= result.loc[0, "similarity_score"] <= 1


def test_defensive_controls_are_explained():
    controls = defensive_controls({
        "vendor": "Example Vendor",
        "product": "Example Product",
        "required_action": "Apply vendor patch",
    })

    names = [item["Control"] for item in controls]
    assert "Patch and vulnerability management" in names
    assert all("Why it may help" in item for item in controls)
