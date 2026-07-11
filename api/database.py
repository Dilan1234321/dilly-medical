"""SQLite store for Dilly Medical.

Career Dilly runs on RDS Postgres; Dilly Medical starts self-contained on
SQLite so the whole product runs from a single process with zero infra.
The schema below is written so a later Postgres migration is mechanical
(no SQLite-only types, JSON stored as TEXT).

Migrations follow the career-Dilly habit: idempotent CREATE/ALTER at startup.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager

from .config import config

_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """Yield a connection. Caller commits; rollback on exception."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    email               TEXT PRIMARY KEY,
    name                TEXT DEFAULT '',
    created_at          TEXT NOT NULL,              -- ISO8601 UTC
    plan                TEXT NOT NULL DEFAULT 'starter',  -- starter | dilly | pro
    subscribed          INTEGER NOT NULL DEFAULT 0,
    edu_verified        INTEGER NOT NULL DEFAULT 0,
    grad_year           INTEGER,                    -- expected undergrad graduation
    target_cycle_year   INTEGER,                    -- AMCAS cycle they plan to enter (e.g. 2028)
    state               TEXT DEFAULT '',            -- residency state (IS/OOS logic)
    gpa                 REAL,                       -- cumulative GPA 0.0-4.0
    gpa_trend           TEXT DEFAULT '',            -- rising | flat | falling | ''
    mcat                INTEGER,                    -- 472-528, NULL = not taken
    mcat_planned_month  TEXT DEFAULT '',            -- e.g. '2027-04'
    include_do          INTEGER NOT NULL DEFAULT 1, -- include DO schools in scouting
    move_count          INTEGER NOT NULL DEFAULT 0, -- shared Moves counter (bucketed)
    move_reset_key      TEXT NOT NULL DEFAULT ''    -- bucket key; count resets when it changes
);

CREATE TABLE IF NOT EXISTS sessions (
    token       TEXT PRIMARY KEY,
    email       TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_codes (
    email       TEXT PRIMARY KEY,
    code        TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

-- Student-owned profile facts. The single source of truth for every read.
-- Everything Dilly says must trace back to a row here (or hours_log).
CREATE TABLE IF NOT EXISTS facts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT NOT NULL,
    category    TEXT NOT NULL,      -- clinical | shadowing | research | service | leadership | course | award | life | letter
    text        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    archived    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_facts_email ON facts(email);

-- The hours ledger: the wedge feature. Voice-first capture on mobile;
-- each entry may carry a fresh reflection (the essay/anecdote bank).
CREATE TABLE IF NOT EXISTS hours_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT NOT NULL,
    category    TEXT NOT NULL,      -- clinical_paid | clinical_volunteer | shadowing | research | volunteering | leadership
    hours       REAL NOT NULL,
    org         TEXT DEFAULT '',    -- where (e.g. 'Tampa General ER')
    role        TEXT DEFAULT '',    -- what (e.g. 'Scribe')
    occurred_on TEXT NOT NULL,      -- ISO date
    reflection  TEXT DEFAULT '',    -- 'anything stick with you today?'
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_hours_email ON hours_log(email);

-- Saved schools (the student's working list) + cached scout reads.
CREATE TABLE IF NOT EXISTS school_list (
    email       TEXT NOT NULL,
    school_id   TEXT NOT NULL,
    added_at    TEXT NOT NULL,
    scout_json  TEXT DEFAULT '',    -- last School Scout read (JSON)
    PRIMARY KEY (email, school_id)
);

-- Crafted artifacts (personal statement drafts, W&A descriptions).
CREATE TABLE IF NOT EXISTS crafts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT NOT NULL,
    kind        TEXT NOT NULL,      -- personal_statement | activity_description
    input_json  TEXT NOT NULL,      -- what it was built from (fact ids etc.)
    output_text TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

-- Readiness reads history (so progress over time is visible).
CREATE TABLE IF NOT EXISTS readiness_reads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT NOT NULL,
    read_json   TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

-- The action trio: 'Add to plan' targets land here.
CREATE TABLE IF NOT EXISTS plan_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT NOT NULL,
    text        TEXT NOT NULL,
    source      TEXT DEFAULT '',    -- readiness | scout | brief | opportunity
    done        INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);
"""


def init_db() -> None:
    """Create tables. Idempotent; called at startup and by tests."""
    with _lock:
        os.makedirs(os.path.dirname(config.db_path), exist_ok=True)
        with get_db() as conn:
            conn.executescript(_SCHEMA)


def to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


def loads(text: str, default=None):
    try:
        return json.loads(text)
    except Exception:
        return default
