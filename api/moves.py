"""Moves metering — one shared counter for every AI action.

Moves that spend a Token: Readiness Read, School Scout, Craft.
Out of Moves -> HTTP 402 with {feature, message}; the mobile client's
fetch interceptor opens the paywall automatically (career-Dilly pattern).

The hours ledger and plan are NEVER metered: logging is the data moat
and must stay permanently free.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from .billing_period import acct_month_bucket, acct_week_bucket
from .database import get_db

PLAN_LIMITS = {
    "starter": 5,   # per week (account-anchored)
    "dilly": 120,   # per month (30-day, signup-anchored)
    "pro": -1,      # uncapped
}


def get_plan_limit(plan: str) -> int:
    return PLAN_LIMITS.get((plan or "starter").lower().strip(), 0)


def reset_key_for_plan(plan: str, email: str, now: datetime | None = None) -> str:
    p = (plan or "starter").lower().strip()
    if p == "pro":
        return "pro"  # uncapped; stable bucket, gate never fires for -1 limits
    if p == "dilly":
        return acct_month_bucket(email, now)
    return acct_week_bucket(email, now)


def get_usage(email: str) -> tuple[int, str]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT move_count, move_reset_key, plan FROM users WHERE email=?", (email,)
        ).fetchone()
        if not row:
            return 0, ""
        count = row["move_count"] or 0
        key = row["move_reset_key"] or ""
        current_key = reset_key_for_plan(row["plan"], email)
        if key != current_key:
            return 0, key  # bucket rotated; effective count is 0
        return count, key


def usage_summary(email: str) -> dict:
    with get_db() as conn:
        row = conn.execute("SELECT plan FROM users WHERE email=?", (email,)).fetchone()
    plan = (row["plan"] if row else "starter") or "starter"
    limit = get_plan_limit(plan)
    used, _ = get_usage(email)
    return {
        "plan": plan,
        "limit": limit,           # -1 = unlimited
        "used": used,
        "remaining": (-1 if limit < 0 else max(0, limit - used)),
        "period": "week" if plan == "starter" else ("month" if plan == "dilly" else "unlimited"),
    }


def spend_move(email: str, feature: str) -> int:
    """Spend one Move or raise 402. Returns the new count."""
    with get_db() as conn:
        row = conn.execute("SELECT plan FROM users WHERE email=?", (email,)).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail={"code": "NO_USER"})
        plan = (row["plan"] or "starter").lower().strip()

    limit = get_plan_limit(plan)
    now = datetime.now(timezone.utc)
    bucket_key = reset_key_for_plan(plan, email, now)
    used, stored_key = get_usage(email)

    if limit >= 0 and used >= limit:
        raise HTTPException(
            status_code=402,
            detail={
                "feature": feature,
                "message": (
                    "You're out of Moves for this "
                    + ("week" if plan == "starter" else "month")
                    + ". Upgrade to keep going — your hours log is always free."
                ),
                "used": used,
                "limit": limit,
            },
        )

    new_count = used + 1
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET move_count=?, move_reset_key=? WHERE email=?",
            (new_count, bucket_key, email),
        )
    return new_count
