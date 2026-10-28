from app.storage import clear_feedback, list_feedback, load_profile, save_feedback, save_profile


def test_profile_round_trip_and_update(tmp_path):
    database = tmp_path / "state.sqlite3"
    profile = {
        "environment": "Cloud",
        "priorities": ["Cloud security", "Vulnerability management"],
        "constraints": ["Prefer open-source tools"],
        "maturity": "Developing",
    }

    save_profile("session-a", profile, database)
    assert load_profile("session-a", database) == profile

    updated = {**profile, "environment": "Hybrid"}
    save_profile("session-a", updated, database)
    assert load_profile("session-a", database) == updated
    assert load_profile("session-b", database) is None


def test_feedback_is_persisted_and_scoped_to_session(tmp_path):
    database = tmp_path / "state.sqlite3"
    entry = {
        "timestamp_utc": "2026-10-28T12:00:00+00:00",
        "reference": "CVE-2025-1234",
        "usefulness_rating": 4,
        "review_outcome": "Relevant to my needs",
        "notes": "Useful context",
    }

    save_feedback("session-a", entry, database)
    save_feedback("session-b", {**entry, "reference": "CVE-2025-5678"}, database)

    assert len(list_feedback("session-a", database)) == 1
    assert list_feedback("session-a", database)[0]["reference"] == "CVE-2025-1234"
    assert len(list_feedback("session-b", database)) == 1

    clear_feedback("session-a", database)
    assert list_feedback("session-a", database) == []
    assert len(list_feedback("session-b", database)) == 1
