"""Craft — turn real facts + reflections into application prose. Spends a Move.

kinds:
  activity_description — a W&A entry (700 chars) for one hours-log activity group
  personal_statement   — a working draft skeleton built ONLY from tagged moments

The no-fabrication rule is the whole trust surface: the deterministic
fallback only rearranges the student's own words; the LLM path carries
NO_FABRICATION_RULES and receives only numbered real facts.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..database import dumps, get_db
from ..deps import require_user
from ..llm import NO_FABRICATION_RULES, complete
from ..moves import spend_move

router = APIRouter(tags=["craft"])


class CraftRequest(BaseModel):
    kind: str                                   # activity_description | personal_statement
    org: str = Field(default="", max_length=120)   # for activity_description: which group
    role: str = Field(default="", max_length=120)
    theme: str = Field(default="", max_length=200)  # optional student-stated theme


def _gather_evidence(email: str, org: str = "", role: str = "") -> tuple[list[str], list[str]]:
    """Return (numbered_facts, numbered_reflections) — the ONLY input Craft may use."""
    with get_db() as conn:
        facts = conn.execute(
            "SELECT id, category, text FROM facts WHERE email=? AND archived=0 ORDER BY id", (email,)
        ).fetchall()
        q = "SELECT id, category, hours, org, role, occurred_on, reflection FROM hours_log WHERE email=?"
        args: list = [email]
        if org:
            q += " AND org=?"
            args.append(org)
        if role:
            q += " AND role=?"
            args.append(role)
        hours = conn.execute(q + " ORDER BY occurred_on", args).fetchall()

    fact_lines = [f"[F{f['id']}] ({f['category']}) {f['text']}" for f in facts]
    refl_lines = [
        f"[H{h['id']}] {h['occurred_on']} — {h['hours']:.0f}h {h['org'] or ''} {h['role'] or ''}: {h['reflection']}"
        for h in hours if (h["reflection"] or "").strip()
    ]
    return fact_lines, refl_lines


def _fallback_activity(org: str, role: str, email: str) -> str:
    """No-LLM path: assemble from the student's own logged words only."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT hours, occurred_on, reflection FROM hours_log WHERE email=? AND org=? ORDER BY occurred_on",
            (email, org),
        ).fetchall()
    if not rows:
        return ""
    total = sum(r["hours"] for r in rows)
    first, last = rows[0]["occurred_on"], rows[-1]["occurred_on"]
    reflections = [r["reflection"].strip() for r in rows if (r["reflection"] or "").strip()]
    body = f"{role or 'Volunteer'}, {org} ({first} to {last}, {total:.0f} hours)."
    if reflections:
        body += " In your own words: " + " / ".join(f'"{r[:160]}"' for r in reflections[:3])
    body += " [Draft assembled from your log — edit into full sentences; every claim above is yours.]"
    return body


@router.post("/craft")
def craft(body: CraftRequest, user: dict = Depends(require_user)):
    if body.kind not in ("activity_description", "personal_statement"):
        raise HTTPException(status_code=400, detail={"code": "BAD_KIND"})

    email = user["email"]
    facts, reflections = _gather_evidence(email, body.org, body.role)
    if body.kind == "activity_description" and not body.org:
        raise HTTPException(status_code=400, detail={"code": "NEED_ORG", "message": "Pick which activity to describe."})
    if not facts and not reflections:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_EVIDENCE",
                    "message": "I can only write from what's real. Log some hours or add facts first — then I'll have material."},
        )

    spend_move(email, "craft")

    if body.kind == "activity_description":
        prompt = (
            f"Write an AMCAS Work & Activities description (under 700 characters) for this activity: "
            f"{body.role or 'volunteer'} at {body.org}. Use ONLY the numbered evidence below. "
            f"Cite nothing that isn't there. Student's theme, if any: {body.theme or 'none'}.\n\n"
            "FACTS:\n" + "\n".join(facts) + "\n\nREFLECTIONS:\n" + "\n".join(reflections)
        )
        max_tokens = 400
    else:
        prompt = (
            "Draft a personal statement WORKING SKELETON (not a finished essay): an opening moment, "
            "2-3 body threads, and a closing thread — each tied to a numbered reflection or fact below. "
            "Where evidence is thin, write [you need a real moment here] instead of inventing one. "
            f"Student's stated theme, if any: {body.theme or 'none'}.\n\n"
            "FACTS:\n" + "\n".join(facts) + "\n\nREFLECTIONS:\n" + "\n".join(reflections)
        )
        max_tokens = 1200

    out = complete(
        system="You are Dilly, helping an undergraduate write their med school application.\n" + NO_FABRICATION_RULES,
        user=prompt,
        max_tokens=max_tokens,
    )
    llm_used = out is not None
    if out is None:
        if body.kind == "activity_description":
            out = _fallback_activity(body.org, body.role, email)
        else:
            threads = "\n".join(f"- Thread from {r}" for r in reflections[:5]) or "- [log reflections after your shifts — they become threads here]"
            out = (
                "Personal statement skeleton (assembled from your own logged moments):\n"
                f"Opening candidate: {reflections[0] if reflections else '[capture one moment that made medicine feel personal]'}\n"
                f"Body threads:\n{threads}\n"
                "Closing: connect your first thread back to the kind of doctor you want to be — in your words."
            )

    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO crafts (email, kind, input_json, output_text, created_at) VALUES (?, ?, ?, ?, ?)",
            (email, body.kind, dumps({"org": body.org, "role": body.role, "theme": body.theme,
                                      "fact_count": len(facts), "reflection_count": len(reflections)}),
             out, datetime.now(timezone.utc).isoformat()),
        )
    return {"id": cur.lastrowid, "kind": body.kind, "output": out, "llm": llm_used,
            "evidence_counts": {"facts": len(facts), "reflections": len(reflections)}}


@router.get("/craft/history")
def craft_history(user: dict = Depends(require_user)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, kind, output_text, created_at FROM crafts WHERE email=? ORDER BY id DESC LIMIT 20",
            (user["email"],),
        ).fetchall()
    return {"crafts": [dict(r) for r in rows]}
