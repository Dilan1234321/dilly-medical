"""Opportunities feed — gap-matched, with 'why I picked this' chips.

Free (browsing costs nothing). Ranking = which readiness dimensions are
weakest for THIS student; each pick explains itself against their real gaps.
"""
from __future__ import annotations

import json
import os

from fastapi import APIRouter, Depends

from ..deps import require_user
from ..readiness import run_readiness_read

router = APIRouter(tags=["opportunities"])

_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "opportunities.json")
_cache: dict | None = None

# opportunity 'fills' tag -> readiness dimension it improves
_FILL_TO_DIM = {
    "clinical": "clinical",
    "shadowing": "shadowing",
    "research": "research_and_service",
    "service": "research_and_service",
    "leadership": "research_and_service",
    "story": "story",
}

_BAND_URGENCY = {"getting_started": 3, "building": 2, "on_track": 1, "strong": 0, "unknown": 1}


def _load() -> dict:
    global _cache
    if _cache is None:
        with open(_DATA_PATH, "r") as f:
            _cache = json.load(f)
    return _cache


@router.get("/opportunities")
def opportunities(user: dict = Depends(require_user)):
    read = run_readiness_read(user)  # deterministic + free (no Move: no LLM, no verdict shown)
    band_by_dim = {d["dimension"]: d["band"] for d in read["dimensions"]}
    open_lane = read["your_open_lane"]

    ranked = []
    for opp in _load()["opportunities"]:
        urgency = 0
        why_chips = []
        for fill in opp["fills"]:
            dim = _FILL_TO_DIM.get(fill, "")
            band = band_by_dim.get(dim, "unknown")
            u = _BAND_URGENCY.get(band, 1)
            urgency = max(urgency, u)
            if u >= 2:
                why_chips.append(f"Fills your {fill.replace('_', ' ')} gap")
            elif u == 1:
                why_chips.append(f"Builds on your {fill.replace('_', ' ')} base")
        if _FILL_TO_DIM.get(opp["fills"][0]) == open_lane:
            urgency += 1
            why_chips.insert(0, "Your open lane right now")
        ranked.append({**opp, "why_chips": why_chips[:3], "_urgency": urgency})

    ranked.sort(key=lambda o: (-o["_urgency"], o["title"]))
    for o in ranked:
        o.pop("_urgency", None)
    return {
        "opportunities": ranked,
        "open_lane": open_lane,
        "data_note": _load()["data_note"],
    }
