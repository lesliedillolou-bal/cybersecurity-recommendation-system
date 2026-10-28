"""Local persistence helpers for anonymous Streamlit profile and feedback data.

The default database is local to this checkout/deployment. Do not use this
prototype storage for sensitive data or a multi-user production service without
authentication, access controls, retention policies, and an appropriate database.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = Path(os.environ.get("CYBERSECURITY_APP_DB", ROOT_DIR / "data" / "app_state.sqlite3"))


def _connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            session_id TEXT PRIMARY KEY,
            profile_json TEXT NOT NULL,
            updated_at_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp_utc TEXT NOT NULL,
            reference TEXT NOT NULL,
            usefulness_rating INTEGER NOT NULL CHECK (usefulness_rating BETWEEN 1 AND 5),
            review_outcome TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_feedback_session_timestamp
            ON feedback(session_id, timestamp_utc);
        """
    )
    return connection


def save_profile(session_id: str, profile: dict[str, Any], db_path: str | Path | None = None) -> None:
    """Persist a profile for an anonymous app session."""
    if not session_id.strip():
        raise ValueError("session_id must not be empty")
    payload = json.dumps(profile, ensure_ascii=False, sort_keys=True)
    with _connect(db_path) as connection:
        connection.execute(
            """INSERT INTO profiles(session_id, profile_json, updated_at_utc)
               VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))
               ON CONFLICT(session_id) DO UPDATE SET
                 profile_json=excluded.profile_json,
                 updated_at_utc=excluded.updated_at_utc""",
            (session_id, payload),
        )


def load_profile(session_id: str, db_path: str | Path | None = None) -> dict[str, Any] | None:
    """Load a profile for an anonymous app session, if one exists."""
    if not session_id.strip():
        return None
    with _connect(db_path) as connection:
        row = connection.execute(
            "SELECT profile_json FROM profiles WHERE session_id = ?", (session_id,)
        ).fetchone()
    return json.loads(row["profile_json"]) if row else None


def save_feedback(session_id: str, entry: dict[str, Any], db_path: str | Path | None = None) -> int:
    """Persist one feedback entry and return its database ID."""
    if not session_id.strip():
        raise ValueError("session_id must not be empty")
    rating = int(entry["usefulness_rating"])
    if not 1 <= rating <= 5:
        raise ValueError("usefulness_rating must be between 1 and 5")
    with _connect(db_path) as connection:
        cursor = connection.execute(
            """INSERT INTO feedback
               (session_id, timestamp_utc, reference, usefulness_rating, review_outcome, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                str(entry["timestamp_utc"]),
                str(entry["reference"]).strip(),
                rating,
                str(entry["review_outcome"]),
                str(entry.get("notes", "")),
            ),
        )
        return int(cursor.lastrowid)


def list_feedback(session_id: str, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Return only feedback entries associated with the supplied session ID."""
    if not session_id.strip():
        return []
    with _connect(db_path) as connection:
        rows = connection.execute(
            """SELECT timestamp_utc, reference, usefulness_rating, review_outcome, notes
               FROM feedback WHERE session_id = ? ORDER BY id""",
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def clear_feedback(session_id: str, db_path: str | Path | None = None) -> None:
    """Delete feedback entries associated with the supplied session ID."""
    if not session_id.strip():
        return
    with _connect(db_path) as connection:
        connection.execute("DELETE FROM feedback WHERE session_id = ?", (session_id,))
