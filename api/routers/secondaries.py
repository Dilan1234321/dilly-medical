"""Secondary essay prompts + Craft integration. Spends a Move per draft."""
from __future__ import annotations

import json
import os

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..database import dumps, get_db
from ..deps import require_user
from ..llm import NO_FABRICATION_RULES, complete
from ..moves import spend_move
from ..school_fit import get_school

router = APIRouter(tags=["secondaries"])

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "secondary_prompts.json")
_cache: dict | None = None


def _load() -> dict:
    global _cache
    if _cache is None:
        with open(_DATA) as f:
            _cache = json.load(f)
    return _cache


@router.get("/secondaries/prompts")
def list_prompts(school_id: str | None = None, user: dict = Depends(require_user)):
    """All secondary prompts: generic + optional school-specific."""
    data = _load()
    school = []
    if school_id:
        if not get_school(school_id):
            raise HTTPException(status_code=404, detail={"code": "NO_SCHOOL"})
        school = data["school_prompts"].get(school_id, [])
    return {
        "generic": data["generic_prompts"],
        "school": school,
        "school_id": school_id,
        "note": "Craft drafts spend a Move and use only your logged facts and reflections.",
    }


class SecondaryCraft(BaseModel):
    school_id: str = ""
    prompt_id: str
    prompt_text: str = Field(min_length=10, max_length=4000)
    char_limit: int = Field(default=2500, ge=500, le=5000)


def _gather_evidence(email: str) -> tuple[list[str], list[str]]:
    with get_db() as conn:
        facts = conn.execute(
            "SELECT id, category, text FROM facts WHERE email=? AND archived=0 ORDER BY id", (email,)
        ).fetchall()
        hours = conn.execute(
            "SELECT id, reflection, voice_transcript, org, role, occurred_on FROM hours_log WHERE email=? ORDER BY occurred_on",
            (email,),
        ).fetchall()
    fact_lines = [f"[F{f['id']}] ({f['category']}) {f['text']}" for f in facts]
    refl = []
    for h in hours:
        text = (h["reflection"] or h.get("voice_transcript") or "").strip()
        if text:
            refl.append(f"[H{h['id']}] {h['occurred_on']} {h['org']} {h['role']}: {text}")
    return fact_lines, refl


@router.post("/secondaries/craft")
def craft_secondary(body: SecondaryCraft, user: dict = Depends(require_user)):
    spend_move(user["email"], "secondary_craft")
    facts, reflections = _gather_evidence(user["email"])
    if not facts and not reflections:
        raise HTTPException(status_code=400, detail={"code": "NO_EVIDENCE",
                    "message": "Log hours with reflections or add facts first."})

    school_name = ""
    if body.school_id:
        s = get_school(body.school_id)
        school_name = s["name"] if s else body.school_id

    prompt = (
        f"Write a secondary essay draft for: {school_name or 'a medical school'}\n"
        f"Prompt: {body.prompt_text}\n"
        f"STRICT character limit: {body.char_limit} characters.\n"
        f"Use ONLY the numbered evidence below. Cite nothing not listed.\n\n"
        f"FACTS:\n" + "\n".join(facts) + "\n\nREFLECTIONS:\n" + "\n".join(reflections)
    )
    out = complete(
        system="You are Dilly, helping an undergraduate draft a med school secondary essay.\n" + NO_FABRICATION_RULES,
        user=prompt,
        max_tokens=1400,
    )
    if not out:
        threads = "\n".join(reflections[:4]) or "[add reflections after shifts]"
        out = (
            f"Working draft skeleton for: {body.prompt_text[:80]}...\n\n"
            f"Open with a moment from your log:\n{reflections[0] if reflections else '[capture a real moment]'}\n\n"
            f"Threads to weave in:\n{threads}\n\n"
            f"[Edit to under {body.char_limit} chars; every claim must be yours.]"
        )

    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO secondary_drafts (email, school_id, prompt_id, output_text, created_at) VALUES (?, ?, ?, ?, ?)",
            (user["email"], body.school_id or "generic", body.prompt_id, out,
             datetime.now(timezone.utc).isoformat()),
        )
    return {"output": out, "char_count": len(out), "limit": body.char_limit, "id": cur.lastrowid}
