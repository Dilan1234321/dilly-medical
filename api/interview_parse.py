"""Parse LLM interview feedback JSON (tolerates markdown wrappers)."""
from __future__ import annotations

import json
import re


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            return None
    return None


def parse_feedback_json(raw: str) -> dict:
    obj = _extract_json(raw)
    if not obj:
        raise ValueError("no json")
    rating = str(obj.get("rating", "needs_work")).lower()
    if rating not in ("strong", "good", "needs_work", "weak"):
        rating = "needs_work"
    return {
        "rating": rating,
        "strengths": list(obj.get("strengths") or [])[:3],
        "improvements": list(obj.get("improvements") or [])[:3],
        "model_opening": str(obj.get("model_opening") or ""),
    }
