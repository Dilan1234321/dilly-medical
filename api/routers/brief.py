"""Weekly brief — cycle-aware 'this week' card for Home. Free."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from ..amcas_calendar import phase_for
from ..database import get_db, loads
from ..deps import require_user
from ..moves import usage_summary

router = APIRouter(tags=["brief"])


@router.get("/brief")
def weekly_brief(user: dict = Depends(require_user)):
    email = user["email"]
    phase = phase_for(date.today(), user.get("target_cycle_year"))

    with get_db() as conn:
        week_hours = conn.execute(
            "SELECT COALESCE(SUM(hours), 0) AS h FROM hours_log WHERE email=? AND occurred_on >= date('now', '-7 days')",
            (email,),
        ).fetchone()["h"]
        streak_row = conn.execute(
            "SELECT COUNT(DISTINCT occurred_on) AS d FROM hours_log WHERE email=? AND occurred_on >= date('now', '-28 days')",
            (email,),
        ).fetchone()["d"]
        last_read = conn.execute(
            "SELECT read_json FROM readiness_reads WHERE email=? ORDER BY id DESC LIMIT 1", (email,)
        ).fetchone()
        open_plan = conn.execute(
            "SELECT COUNT(*) AS n FROM plan_items WHERE email=? AND done=0", (email,)
        ).fetchone()["n"]

    open_lane = None
    this_week = phase["move"]
    if last_read:
        read = loads(last_read["read_json"], {})
        open_lane = read.get("your_open_lane")
        if read.get("this_week"):
            this_week = read["this_week"]

    return {
        "phase": phase,
        "hours_this_week": week_hours,
        "active_days_month": streak_row,
        "open_lane": open_lane,
        "this_week": this_week,
        "open_plan_items": open_plan,
        "moves": usage_summary(email),
    }
