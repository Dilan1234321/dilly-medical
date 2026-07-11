"""Health, Moves usage, and subscription plumbing (Stripe-ready stubs)."""
from __future__ import annotations

import os
import subprocess

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..database import get_db
from ..deps import require_user
from ..llm import is_llm_available
from ..moves import PLAN_LIMITS, usage_summary

router = APIRouter()


@router.get("/health", tags=["health"])
def health():
    commit = ""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)), text=True, timeout=3,
        ).strip()
    except Exception:
        pass
    db_ok = True
    db_backend = "postgres" if config.database_url else "sqlite"
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
    except Exception:
        db_ok = False
    return {"ok": db_ok, "commit": commit, "llm": is_llm_available(), "db": db_backend}


@router.get("/moves/usage", tags=["moves"])
def moves_usage(user: dict = Depends(require_user)):
    return usage_summary(user["email"])


class PlanChange(BaseModel):
    plan: str


@router.post("/subscription/set-plan", tags=["billing"])
def set_plan(body: PlanChange, user: dict = Depends(require_user)):
    """Dev/testing plan switch. Production replaces this with the Stripe
    webhook (Payment Links, same as career Dilly). Kept explicit so the
    mobile paywall flow is fully exercisable before Stripe is wired."""
    plan = body.plan.lower().strip()
    if plan not in PLAN_LIMITS:
        raise HTTPException(status_code=400, detail={"code": "BAD_PLAN", "plans": list(PLAN_LIMITS)})
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET plan=?, subscribed=? WHERE email=?",
            (plan, 0 if plan == "starter" else 1, user["email"]),
        )
    return {"plan": plan}


@router.post("/subscription/cancel", tags=["billing"])
def cancel(user: dict = Depends(require_user)):
    # Career-Dilly lesson baked in: clear BOTH plan and subscribed flag.
    with get_db() as conn:
        conn.execute("UPDATE users SET plan='starter', subscribed=0 WHERE email=?", (user["email"],))
    return {"plan": "starter", "subscribed": False}
