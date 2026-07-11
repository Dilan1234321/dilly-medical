"""Email + 6-digit code auth (same shape as career Dilly).

Dev mode returns the code in the response; production plugs in an email
provider (Resend) without changing the endpoints.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from ..config import config
from ..database import get_db
from ..deps import require_user

router = APIRouter(tags=["auth"])


class SendCodeRequest(BaseModel):
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/auth/send-code")
def send_code(body: SendCodeRequest):
    code = f"{secrets.randbelow(1_000_000):06d}"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO auth_codes (email, code, created_at) VALUES (?, ?, ?) "
            "ON CONFLICT(email) DO UPDATE SET code=excluded.code, created_at=excluded.created_at",
            (body.email.lower(), code, _now()),
        )
    resp = {"sent": True}
    if config.dev_mode:
        resp["dev_code"] = code  # no email provider wired yet
    return resp


@router.post("/auth/verify-code")
def verify_code(body: VerifyCodeRequest):
    email = body.email.lower()
    with get_db() as conn:
        row = conn.execute("SELECT code FROM auth_codes WHERE email=?", (email,)).fetchone()
        if not row or row["code"] != body.code.strip():
            raise HTTPException(status_code=401, detail={"code": "BAD_CODE", "message": "That code didn't match. Try again."})
        conn.execute("DELETE FROM auth_codes WHERE email=?", (email,))
        user = conn.execute("SELECT email FROM users WHERE email=?", (email,)).fetchone()
        if not user:
            conn.execute(
                "INSERT INTO users (email, created_at, edu_verified) VALUES (?, ?, ?)",
                (email, _now(), 1 if email.endswith(".edu") else 0),
            )
        token = secrets.token_hex(24)
        conn.execute("INSERT INTO sessions (token, email, created_at) VALUES (?, ?, ?)", (token, email, _now()))
    return {"token": token, "email": email}


@router.get("/auth/me")
def me(user: dict = Depends(require_user)):
    safe = {k: user[k] for k in (
        "email", "name", "plan", "subscribed", "edu_verified", "grad_year",
        "target_cycle_year", "state", "gpa", "gpa_trend", "mcat",
        "mcat_planned_month", "include_do",
    )}
    return safe
