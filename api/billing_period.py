"""Account-anchored Move buckets — same semantics as career Dilly.

Free (starter) rotates WEEKLY anchored to signup; the Dilly tier rotates
MONTHLY (30-day, signup-anchored); Pro is uncapped. Falls back to ISO
calendar buckets when signup is unknown so it still rotates + never crashes.
"""
from __future__ import annotations

from datetime import datetime, timezone


def _user_created_at(email: str):
    try:
        from .database import get_db

        with get_db() as conn:
            row = conn.execute(
                "SELECT created_at FROM users WHERE LOWER(email)=LOWER(?)", (email,)
            ).fetchone()
            if row and row["created_at"]:
                dt = datetime.fromisoformat(row["created_at"])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
    except Exception:
        pass
    return None


def acct_week_bucket(email: str, now: datetime | None = None) -> str:
    n = now or datetime.now(timezone.utc)
    created = _user_created_at(email)
    if created is None:
        iso = n.isocalendar()
        return f"isoW{iso[0]}-{iso[1]:02d}"
    days = max(0, (n.date() - created.date()).days)
    return f"acctW{days // 7}"


def acct_month_bucket(email: str, now: datetime | None = None) -> str:
    n = now or datetime.now(timezone.utc)
    created = _user_created_at(email)
    if created is None:
        return f"isoM{n.year}-{n.month:02d}"
    days = max(0, (n.date() - created.date()).days)
    return f"acctM{days // 30}"
