"""Schools: browse list (free), manage my list (free), Scout a school (Move)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from ..database import dumps, get_db, loads
from ..deps import require_user
from ..llm import NO_FABRICATION_RULES, complete
from ..moves import spend_move
from ..school_fit import get_school, load_schools, rank_all_schools, scout_school

router = APIRouter(tags=["schools"])


@router.get("/schools")
def list_schools(user: dict = Depends(require_user)):
    include_do = bool(user.get("include_do", 1))
    with get_db() as conn:
        saved = {r["school_id"] for r in conn.execute(
            "SELECT school_id FROM school_list WHERE email=?", (user["email"],)
        ).fetchall()}
    schools = rank_all_schools(user, include_do=include_do)
    for s in schools:
        s["saved"] = s["id"] in saved
    return {"schools": schools, "data_note": load_schools()["data_note"]}


@router.post("/schools/{school_id}/save")
def save_school(school_id: str, user: dict = Depends(require_user)):
    if not get_school(school_id):
        raise HTTPException(status_code=404, detail={"code": "NO_SCHOOL"})
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO school_list (email, school_id, added_at) VALUES (?, ?, ?)",
            (user["email"], school_id, datetime.now(timezone.utc).isoformat()),
        )
    return {"saved": True}


@router.delete("/schools/{school_id}/save")
def unsave_school(school_id: str, user: dict = Depends(require_user)):
    with get_db() as conn:
        conn.execute("DELETE FROM school_list WHERE email=? AND school_id=?", (user["email"], school_id))
    return {"saved": False}


@router.get("/schools/my-list")
def my_list(user: dict = Depends(require_user)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT school_id, scout_json, added_at FROM school_list WHERE email=? ORDER BY added_at",
            (user["email"],),
        ).fetchall()
    out = []
    for r in rows:
        school = get_school(r["school_id"])
        if not school:
            continue
        out.append({
            "school": {k: school[k] for k in ("id", "name", "type", "state", "city")},
            "scout": loads(r["scout_json"]) if r["scout_json"] else None,
        })
    return {"list": out}


@router.post("/schools/{school_id}/scout")
def scout(school_id: str, user: dict = Depends(require_user)):
    """School Scout — spends a Move. Cached onto the student's list."""
    if not get_school(school_id):
        raise HTTPException(status_code=404, detail={"code": "NO_SCHOOL"})
    spend_move(user["email"], "school_scout")
    read = scout_school(user, school_id)

    narrative = complete(
        system=(
            "You are Dilly, a warm, honest pre-med coach. Rewrite this school "
            "fit read as 3-4 plain sentences addressed to the student. Name the "
            "school. Be honest about the verdict without being cruel.\n"
            + NO_FABRICATION_RULES
        ),
        user=dumps(read),
        max_tokens=400,
    )
    if narrative:
        read["narrative"] = narrative

    with get_db() as conn:
        conn.execute(
            "INSERT INTO school_list (email, school_id, added_at, scout_json) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(email, school_id) DO UPDATE SET scout_json=excluded.scout_json",
            (user["email"], school_id, datetime.now(timezone.utc).isoformat(), dumps(read)),
        )
    return read
