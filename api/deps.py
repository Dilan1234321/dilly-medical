"""Auth dependency: bearer session token -> user row."""
from __future__ import annotations

from fastapi import Header, HTTPException

from .database import get_db, to_dict


def require_user(authorization: str = Header(default="")) -> dict:
    token = ""
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail={"code": "NO_TOKEN"})
    with get_db() as conn:
        sess = conn.execute("SELECT email FROM sessions WHERE token=?", (token,)).fetchone()
        if not sess:
            raise HTTPException(status_code=401, detail={"code": "BAD_TOKEN"})
        user = conn.execute("SELECT * FROM users WHERE email=?", (sess["email"],)).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail={"code": "NO_USER"})
        return to_dict(user)
