"""MMI + traditional interview practice. Spends a Move per feedback round."""
from __future__ import annotations

import json
import os
import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..database import dumps, get_db, loads
from ..deps import require_user
from ..llm import NO_FABRICATION_RULES, complete
from ..moves import spend_move

router = APIRouter(tags=["interview"])

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "mmi_stations.json")


def _stations() -> list[dict]:
    with open(_DATA) as f:
        return json.load(f)["stations"]


class StartSession(BaseModel):
    count: int = Field(default=3, ge=1, le=6)
    kind: str = "mmi"


class AnswerBody(BaseModel):
    session_id: int
    station_index: int
    answer: str = Field(min_length=10, max_length=8000)


@router.get("/interview/stations")
def list_stations(user: dict = Depends(require_user)):
    """Preview station types (free)."""
    return {"stations": _stations(), "note": "Full feedback spends a Move per session round."}


@router.post("/interview/session")
def start_session(body: StartSession, user: dict = Depends(require_user)):
    """Pick random MMI stations for a practice round (free to start)."""
    pool = _stations()
    picked = random.sample(pool, min(body.count, len(pool)))
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO interview_sessions (email, kind, stations_json, answers_json, created_at) VALUES (?, ?, ?, '[]', ?)",
            (user["email"], body.kind, dumps(picked), datetime.now(timezone.utc).isoformat()),
        )
        sid = cur.lastrowid
    return {"session_id": sid, "stations": picked}


@router.post("/interview/feedback")
def feedback(body: AnswerBody, user: dict = Depends(require_user)):
    """Score one station answer. Spends a Move."""
    spend_move(user["email"], "interview_feedback")
    with get_db() as conn:
        row = conn.execute(
            "SELECT stations_json, answers_json FROM interview_sessions WHERE id=? AND email=?",
            (body.session_id, user["email"]),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail={"code": "NO_SESSION"})
    stations = loads(row["stations_json"], [])
    if body.station_index < 0 or body.station_index >= len(stations):
        raise HTTPException(status_code=400, detail={"code": "BAD_INDEX"})
    station = stations[body.station_index]

    prompt = (
        f"Station type: {station['type']}\nPrompt: {station['prompt']}\n"
        f"Probe: {station.get('probe', '')}\nRubric: {', '.join(station.get('rubric', []))}\n\n"
        f"Student answer:\n{body.answer}\n\n"
        "Return JSON with keys: rating (strong|good|needs_work|weak), "
        "strengths (array of 2 short strings), improvements (array of 2 short strings), "
        "model_opening (one sentence they could use to start stronger). "
        "Be direct and kind. No numeric scores."
    )
    raw = complete(
        system="You are Dilly, an MMI interview coach for pre-med undergraduates.\n" + NO_FABRICATION_RULES,
        user=prompt,
        max_tokens=600,
    )

    if raw:
        try:
            from ..interview_parse import parse_feedback_json
            fb = parse_feedback_json(raw)
        except Exception:
            fb = _fallback_feedback(body.answer, station)
    else:
        fb = _fallback_feedback(body.answer, station)

    with get_db() as conn:
        sess = conn.execute(
            "SELECT answers_json FROM interview_sessions WHERE id=? AND email=?",
            (body.session_id, user["email"]),
        ).fetchone()
        answers = loads(sess["answers_json"], [])
        answers.append({"station_index": body.station_index, "answer": body.answer, "feedback": fb})
        conn.execute(
            "UPDATE interview_sessions SET answers_json=? WHERE id=? AND email=?",
            (dumps(answers), body.session_id, user["email"]),
        )
    return {"station": station, "feedback": fb}


def _fallback_feedback(answer: str, station: dict) -> dict:
    words = len(answer.split())
    rating = "strong" if words >= 120 else "good" if words >= 70 else "needs_work" if words >= 35 else "weak"
    return {
        "rating": rating,
        "strengths": [
            "You engaged with the scenario directly.",
            f"You spoke ~{words} words — {'solid length' if words >= 70 else 'room to build out'}.",
        ],
        "improvements": [
            f"Name one principle from the rubric explicitly: {', '.join(station.get('rubric', [])[:2])}.",
            "End with your concrete next action, not a general value statement.",
        ],
        "model_opening": "I would start by naming who is affected and what matters most in this scenario.",
    }
