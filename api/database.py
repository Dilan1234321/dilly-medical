"""Database layer — SQLite locally, Postgres on Railway (DATABASE_URL).

All routers use `?` placeholders; the adapter translates to `%s` for Postgres.
Row access is dict-like via fetchone/fetchall helpers.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any

from .config import config

_lock = threading.Lock()
_pg_pool = None


def _use_postgres() -> bool:
    return bool(config.database_url)


class _Row(dict):
    """Dict row with attribute access for compatibility."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class _Cursor:
    """Unified cursor for sqlite3 and psycopg2."""

    def __init__(self, raw_cur, is_pg: bool, conn: "DbConn"):
        self._cur = raw_cur
        self._is_pg = is_pg
        self._conn = conn
        self.lastrowid: int | None = None

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        if self._is_pg:
            return _Row(row)
        return _Row(dict(row))

    def fetchall(self):
        if self._is_pg:
            return [_Row(r) for r in self._cur.fetchall()]
        return [_Row(dict(r)) for r in self._cur.fetchall()]


class DbConn:
    """Thin adapter over sqlite3 or psycopg2 connections."""

    def __init__(self, raw, is_pg: bool):
        self._raw = raw
        self._is_pg = is_pg

    def execute(self, sql: str, params: tuple | list = ()) -> _Cursor:
        sql = self._adapt(sql)
        if self._is_pg:
            import psycopg2.extras
            cur = self._raw.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params)
            wrapper = _Cursor(cur, True, self)
            if sql.strip().upper().startswith("INSERT") and "RETURNING" not in sql.upper():
                try:
                    cur.execute("SELECT lastval()")
                    wrapper.lastrowid = int(cur.fetchone()["lastval"])
                except Exception:
                    wrapper.lastrowid = None
            elif "RETURNING" in sql.upper():
                row = cur.fetchone()
                wrapper.lastrowid = int(row["id"]) if row and "id" in row else None
            return wrapper
        cur = self._raw.execute(sql, params)
        wrapper = _Cursor(cur, False, self)
        wrapper.lastrowid = cur.lastrowid
        return wrapper

    def executemany(self, sql: str, seq):
        sql = self._adapt(sql)
        if self._is_pg:
            import psycopg2.extras
            cur = self._raw.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.executemany(sql, seq)
            return _Cursor(cur, True, self)
        cur = self._raw.executemany(sql, seq)
        return _Cursor(cur, False, self)

    def executescript(self, sql: str):
        if self._is_pg:
            for stmt in _split_sql(sql):
                s = self._adapt(stmt.strip())
                if s:
                    try:
                        self.execute(s)
                    except Exception:
                        pass
            return
        return self._raw.executescript(sql)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def _adapt(self, sql: str) -> str:
        if not self._is_pg:
            return sql
        out = sql.replace("?", "%s")
        # Postgres: ON CONFLICT ... DO UPDATE needs different syntax sometimes
        if "INSERT OR IGNORE" in out.upper():
            out = out.replace("INSERT OR IGNORE", "INSERT").replace("insert or ignore", "INSERT")
            if "ON CONFLICT" not in out.upper():
                # append DO NOTHING if we can find the table PK — skip for simplicity
                pass
        return out


def _split_sql(script: str) -> list[str]:
    return [s for s in script.split(";") if s.strip()]


def _connect_sqlite() -> DbConn:
    os.makedirs(os.path.dirname(config.db_path) or ".", exist_ok=True)
    raw = sqlite3.connect(config.db_path, timeout=30)
    raw.row_factory = sqlite3.Row
    raw.execute("PRAGMA journal_mode=WAL")
    raw.execute("PRAGMA foreign_keys=ON")
    return DbConn(raw, False)


def _connect_pg() -> DbConn:
    global _pg_pool
    if _pg_pool is None:
        import psycopg2.pool
        _pg_pool = psycopg2.pool.ThreadedConnectionPool(1, 10, config.database_url)
    raw = _pg_pool.getconn()
    return DbConn(raw, True)


@contextmanager
def get_db():
    conn = _connect_pg() if _use_postgres() else _connect_sqlite()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if _use_postgres():
            _pg_pool.putconn(conn._raw)
        else:
            conn._raw.close()


_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    name TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'starter',
    subscribed INTEGER NOT NULL DEFAULT 0,
    edu_verified INTEGER NOT NULL DEFAULT 0,
    grad_year INTEGER,
    target_cycle_year INTEGER,
    state TEXT DEFAULT '',
    gpa REAL,
    gpa_trend TEXT DEFAULT '',
    mcat INTEGER,
    mcat_planned_month TEXT DEFAULT '',
    include_do INTEGER NOT NULL DEFAULT 1,
    move_count INTEGER NOT NULL DEFAULT 0,
    move_reset_key TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_codes (
    email TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    category TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_facts_email ON facts(email);

CREATE TABLE IF NOT EXISTS hours_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    category TEXT NOT NULL,
    hours REAL NOT NULL,
    org TEXT DEFAULT '',
    role TEXT DEFAULT '',
    occurred_on TEXT NOT NULL,
    reflection TEXT DEFAULT '',
    voice_transcript TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_hours_email ON hours_log(email);

CREATE TABLE IF NOT EXISTS school_list (
    email TEXT NOT NULL,
    school_id TEXT NOT NULL,
    added_at TEXT NOT NULL,
    scout_json TEXT DEFAULT '',
    PRIMARY KEY (email, school_id)
);

CREATE TABLE IF NOT EXISTS crafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    kind TEXT NOT NULL,
    input_json TEXT NOT NULL,
    output_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS readiness_reads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    read_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    text TEXT NOT NULL,
    source TEXT DEFAULT '',
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS live_opportunities (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    org TEXT DEFAULT '',
    url TEXT DEFAULT '',
    category TEXT NOT NULL,
    source TEXT NOT NULL,
    location TEXT DEFAULT '',
    paid INTEGER NOT NULL DEFAULT 0,
    description TEXT DEFAULT '',
    fetched_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_live_opp_cat ON live_opportunities(category);

CREATE TABLE IF NOT EXISTS interview_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    kind TEXT NOT NULL,
    stations_json TEXT NOT NULL,
    answers_json TEXT DEFAULT '[]',
    feedback_json TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS secondary_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    school_id TEXT NOT NULL,
    prompt_id TEXT NOT NULL,
    output_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _migrate(conn: DbConn):
    """Idempotent column adds."""
    alters = [
        "ALTER TABLE hours_log ADD COLUMN voice_transcript TEXT DEFAULT ''",
    ]
    for sql in alters:
        try:
            conn.execute(sql)
        except Exception:
            pass


def _schema_sql() -> str:
    """SQLite locally; SERIAL PKs on Postgres (Railway)."""
    if not _use_postgres():
        return _SCHEMA_SQLITE
    return _SCHEMA_SQLITE.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")


def init_db() -> None:
    with _lock:
        with get_db() as conn:
            conn.executescript(_schema_sql())
            _migrate(conn)


def to_dict(row: Any | None) -> dict | None:
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return dict(row)


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


def loads(text: str, default=None):
    try:
        return json.loads(text)
    except Exception:
        return default


def insert_returning_id(conn: DbConn, sql: str, params: tuple) -> int:
    """Cross-db insert that returns new row id."""
    if _use_postgres() and "RETURNING" not in sql.upper():
        sql = sql.rstrip().rstrip(";") + " RETURNING id"
    cur = conn.execute(sql, params)
    if cur.lastrowid:
        return int(cur.lastrowid)
    return 0
