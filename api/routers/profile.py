"""Profile + facts. Facts are the source of truth for every read."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..database import get_db
from ..deps import require_user

router = APIRouter(tags=["profile"])

FACT_CATEGORIES = [
    "clinical", "shadowing", "research", "service",
    "leadership", "course", "award", "life", "letter",
]

_PATCHABLE = {
    "name", "grad_year", "target_cycle_year", "state", "gpa",
    "gpa_trend", "mcat", "mcat_planned_month", "include_do",
}


class ProfilePatch(BaseModel):
    name: str | None = None
    grad_year: int | None = Field(default=None, ge=2020, le=2040)
    target_cycle_year: int | None = Field(default=None, ge=2024, le=2040)
    state: str | None = Field(default=None, max_length=2)
    gpa: float | None = Field(default=None, ge=0.0, le=4.0)
    gpa_trend: str | None = None
    mcat: int | None = Field(default=None, ge=472, le=528)
    mcat_planned_month: str | None = None
    include_do: bool | None = None


class FactCreate(BaseModel):
    category: str
    text: str = Field(min_length=3, max_length=600)


@router.patch("/profile")
def patch_profile(body: ProfilePatch, user: dict = Depends(require_user)):
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if k in _PATCHABLE}
    if not updates:
        return {"updated": False}
    sets = ", ".join(f"{k}=?" for k in updates)
    with get_db() as conn:
        conn.execute(f"UPDATE users SET {sets} WHERE email=?", (*updates.values(), user["email"]))
    return {"updated": True, "fields": list(updates)}


@router.get("/facts")
def list_facts(user: dict = Depends(require_user)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, category, text, created_at FROM facts WHERE email=? AND archived=0 ORDER BY id DESC",
            (user["email"],),
        ).fetchall()
    return {"facts": [dict(r) for r in rows], "categories": FACT_CATEGORIES}


@router.post("/facts")
def add_fact(body: FactCreate, user: dict = Depends(require_user)):
    if body.category not in FACT_CATEGORIES:
        raise HTTPException(status_code=400, detail={"code": "BAD_CATEGORY", "categories": FACT_CATEGORIES})
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO facts (email, category, text, created_at) VALUES (?, ?, ?, ?)",
            (user["email"], body.category, body.text.strip(), datetime.now(timezone.utc).isoformat()),
        )
        fact_id = cur.lastrowid
    return {"id": fact_id}


@router.delete("/facts/{fact_id}")
def archive_fact(fact_id: int, user: dict = Depends(require_user)):
    with get_db() as conn:
        conn.execute("UPDATE facts SET archived=1 WHERE id=? AND email=?", (fact_id, user["email"]))
    return {"archived": True}


@router.get("/plan-items")
def list_plan(user: dict = Depends(require_user)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, text, source, done, created_at FROM plan_items WHERE email=? ORDER BY done, id DESC",
            (user["email"],),
        ).fetchall()
    return {"items": [dict(r) for r in rows]}


class PlanCreate(BaseModel):
    text: str = Field(min_length=3, max_length=400)
    source: str = ""


@router.post("/plan-items")
def add_plan(body: PlanCreate, user: dict = Depends(require_user)):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO plan_items (email, text, source, created_at) VALUES (?, ?, ?, ?)",
            (user["email"], body.text.strip(), body.source, datetime.now(timezone.utc).isoformat()),
        )
    return {"id": cur.lastrowid}


@router.patch("/plan-items/{item_id}")
def toggle_plan(item_id: int, user: dict = Depends(require_user)):
    with get_db() as conn:
        conn.execute(
            "UPDATE plan_items SET done = 1 - done WHERE id=? AND email=?",
            (item_id, user["email"]),
        )
    return {"toggled": True}
