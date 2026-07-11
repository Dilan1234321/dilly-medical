"""Readiness Read endpoints. Running a read spends a Move."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ..database import dumps, get_db, loads
from ..deps import require_user
from ..llm import NO_FABRICATION_RULES, complete
from ..moves import spend_move
from ..readiness import run_readiness_read

router = APIRouter(tags=["readiness"])


@router.post("/readiness/read")
def readiness_read(user: dict = Depends(require_user)):
    spend_move(user["email"], "readiness_read")
    read = run_readiness_read(user)

    # Optional LLM warm pass: rewrite each dimension's headline in Dilly's
    # voice. Bands/evidence/moves stay rule-computed — never hallucinated.
    narrative = complete(
        system=(
            "You are Dilly, a warm, honest pre-med coach for undergraduates. "
            "Rewrite the following readiness read as 3-5 plain sentences a "
            "student would want to screenshot. Speak to them directly.\n"
            + NO_FABRICATION_RULES
        ),
        user=dumps(read),
        max_tokens=500,
    )
    if narrative:
        read["narrative"] = narrative

    with get_db() as conn:
        conn.execute(
            "INSERT INTO readiness_reads (email, read_json, created_at) VALUES (?, ?, ?)",
            (user["email"], dumps(read), datetime.now(timezone.utc).isoformat()),
        )
    return read


@router.get("/readiness/latest")
def readiness_latest(user: dict = Depends(require_user)):
    """Free: return the most recent read (Home teaser). No Move spent."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT read_json, created_at FROM readiness_reads WHERE email=? ORDER BY id DESC LIMIT 1",
            (user["email"],),
        ).fetchone()
    if not row:
        return {"read": None}
    return {"read": loads(row["read_json"]), "created_at": row["created_at"]}


@router.get("/readiness/history")
def readiness_history(user: dict = Depends(require_user)):
    """Band progression over time — progress the student can feel."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT read_json, created_at FROM readiness_reads WHERE email=? ORDER BY id",
            (user["email"],),
        ).fetchall()
    out = []
    for r in rows:
        read = loads(r["read_json"], {})
        out.append({
            "created_at": r["created_at"],
            "bands": {d["dimension"]: d["band"] for d in read.get("dimensions", [])},
        })
    return {"history": out}
