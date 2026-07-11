"""The hours ledger — the wedge. Permanently free, never metered.

Log entries carry an optional reflection ('anything stick with you today?').
The export endpoint assembles an AMCAS Work & Activities style summary
grouped by org/role — the two-years-later spreadsheet panic, deleted.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..database import get_db
from ..deps import require_user

router = APIRouter(tags=["hours"])

HOUR_CATEGORIES = [
    "clinical_paid", "clinical_volunteer", "shadowing",
    "research", "volunteering", "leadership",
]

CATEGORY_LABELS = {
    "clinical_paid": "Paid clinical",
    "clinical_volunteer": "Clinical volunteering",
    "shadowing": "Physician shadowing",
    "research": "Research",
    "volunteering": "Community service (non-clinical)",
    "leadership": "Leadership",
}


class HoursCreate(BaseModel):
    category: str
    hours: float = Field(gt=0, le=24)
    org: str = Field(default="", max_length=120)
    role: str = Field(default="", max_length=120)
    occurred_on: str = ""          # ISO date; defaults to today
    reflection: str = Field(default="", max_length=2000)


@router.get("/hours")
def list_hours(user: dict = Depends(require_user)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, category, hours, org, role, occurred_on, reflection, created_at "
            "FROM hours_log WHERE email=? ORDER BY occurred_on DESC, id DESC",
            (user["email"],),
        ).fetchall()
    entries = [dict(r) for r in rows]
    totals: dict[str, float] = {}
    for e in entries:
        totals[e["category"]] = totals.get(e["category"], 0.0) + e["hours"]
    return {
        "entries": entries,
        "totals": totals,
        "clinical_total": totals.get("clinical_paid", 0) + totals.get("clinical_volunteer", 0),
        "categories": HOUR_CATEGORIES,
        "labels": CATEGORY_LABELS,
    }


@router.post("/hours")
def log_hours(body: HoursCreate, user: dict = Depends(require_user)):
    if body.category not in HOUR_CATEGORIES:
        raise HTTPException(status_code=400, detail={"code": "BAD_CATEGORY", "categories": HOUR_CATEGORIES})
    occurred = body.occurred_on or datetime.now(timezone.utc).date().isoformat()
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO hours_log (email, category, hours, org, role, occurred_on, reflection, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user["email"], body.category, body.hours, body.org.strip(), body.role.strip(),
             occurred, body.reflection.strip(), datetime.now(timezone.utc).isoformat()),
        )
    return {"id": cur.lastrowid, "captured_reflection": bool(body.reflection.strip())}


@router.delete("/hours/{entry_id}")
def delete_hours(entry_id: int, user: dict = Depends(require_user)):
    with get_db() as conn:
        conn.execute("DELETE FROM hours_log WHERE id=? AND email=?", (entry_id, user["email"]))
    return {"deleted": True}


@router.get("/hours/export")
def export_work_and_activities(user: dict = Depends(require_user)):
    """AMCAS Work & Activities style export: grouped by (org, role, category),
    total hours, date range, and the student's own reflections as raw material."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT category, hours, org, role, occurred_on, reflection FROM hours_log "
            "WHERE email=? ORDER BY occurred_on",
            (user["email"],),
        ).fetchall()

    groups: dict[tuple, dict] = {}
    for r in rows:
        key = (r["org"] or "—", r["role"] or "—", r["category"])
        g = groups.setdefault(key, {
            "org": r["org"] or "", "role": r["role"] or "",
            "category": r["category"], "label": CATEGORY_LABELS.get(r["category"], r["category"]),
            "total_hours": 0.0, "first_date": r["occurred_on"], "last_date": r["occurred_on"],
            "reflections": [],
        })
        g["total_hours"] += r["hours"]
        g["last_date"] = r["occurred_on"]
        if (r["reflection"] or "").strip():
            g["reflections"].append({"date": r["occurred_on"], "text": r["reflection"]})

    activities = sorted(groups.values(), key=lambda g: -g["total_hours"])
    return {
        "activities": activities,
        "note": "AMCAS Work & Activities allows 15 entries, 700 characters each "
                "(1325 for up to 3 'most meaningful'). Your reflections below are "
                "your raw material — Craft can turn any group into a description.",
    }
