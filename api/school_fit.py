"""School Scout — the fit read on one specific med school.

Verdict is the pre-med convention (likely / target / reach / far_reach) plus
an in-state/out-of-state adjustment and a mission-fit read that cites the
student's real facts. Deterministic; the LLM may warm the prose but never
decides the verdict.

Never outputs an admission probability. Never recommends Caribbean schools
(none are in the dataset by design).
"""
from __future__ import annotations

import json
import os

from . import benchmarks
from .database import get_db

_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "med_schools.json")
_EXTENDED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "med_schools_extended.json")
_cache: dict | None = None


def load_schools() -> dict:
    global _cache
    if _cache is None:
        with open(_DATA_PATH, "r") as f:
            _cache = json.load(f)
        if os.path.isfile(_EXTENDED_PATH):
            with open(_EXTENDED_PATH, "r") as f:
                extra = json.load(f)
            seen = {s["id"] for s in _cache["schools"]}
            for s in extra.get("schools", []):
                if s["id"] not in seen:
                    _cache["schools"].append(s)
                    seen.add(s["id"])
    return _cache


def get_school(school_id: str) -> dict | None:
    for s in load_schools()["schools"]:
        if s["id"] == school_id:
            return s
    return None


# Mission tag -> (fact/hours categories that evidence it, plain-english need)
_MISSION_EVIDENCE = {
    "research": (("research",), ("research",), "sustained research"),
    "academic_medicine": (("research",), ("research",), "scholarly depth"),
    "primary_care": (("clinical",), ("clinical_paid", "clinical_volunteer"), "longitudinal patient contact"),
    "service": (("service", "leadership"), ("volunteering", "leadership"), "sustained community service"),
    "community": (("service", "leadership"), ("volunteering", "leadership"), "community commitment"),
    "urban_underserved": (("service", "clinical"), ("volunteering", "clinical_volunteer"), "work with underserved communities"),
    "rural": (("service", "clinical"), ("volunteering", "clinical_volunteer"), "rural or underserved exposure"),
    "public_health": (("service", "research"), ("volunteering", "research"), "population-health work"),
    "innovation": (("research", "leadership"), ("research",), "building things"),
}


def _stat_distance(user: dict, school: dict) -> tuple[str, list[str]]:
    """Return (stat_band, evidence). stat_band: above | near | below | far_below | unknown."""
    gpa, mcat = user.get("gpa"), user.get("mcat")
    ev = []
    if gpa is None:
        return "unknown", ["Add your GPA to sharpen this read."]

    gpa_gap = gpa - school["median_gpa"]
    ev.append(f"Your GPA {gpa:.2f} vs their ~{school['median_gpa']:.2f} median.")
    if mcat is not None:
        mcat_gap = mcat - school["median_mcat"]
        ev.append(f"Your MCAT {mcat} vs their ~{school['median_mcat']} median.")
    else:
        mcat_gap = None
        ev.append(f"No MCAT yet — their median is ~{school['median_mcat']}, so that's your target number.")

    def _bucket(g_gap: float, m_gap: float | None) -> str:
        score = 0
        score += 1 if g_gap >= 0 else (-1 if g_gap > -0.15 else -2)
        if m_gap is not None:
            score += 1 if m_gap >= 0 else (-1 if m_gap > -4 else -2)
        if score >= 1:
            return "above"
        if score == 0:
            return "near"
        if score >= -2:
            return "below"
        return "far_below"

    return _bucket(gpa_gap, mcat_gap), ev


def _mission_fit(email: str, school: dict) -> tuple[int, list[str], list[str]]:
    """Return (hits, evidence_bullets, gap_needs)."""
    with get_db() as conn:
        facts = [dict(r) for r in conn.execute(
            "SELECT id, category, text FROM facts WHERE email=? AND archived=0", (email,)
        ).fetchall()]
        hour_rows = [dict(r) for r in conn.execute(
            "SELECT id, category, hours, org FROM hours_log WHERE email=?", (email,)
        ).fetchall()]

    hits, evidence, gaps = 0, [], []
    for tag in school.get("mission_tags", []):
        spec = _MISSION_EVIDENCE.get(tag)
        if not spec:
            continue
        fact_cats, hour_cats, need = spec
        fact_hit = next((f for f in facts if f["category"] in fact_cats), None)
        hour_total = sum(h["hours"] for h in hour_rows if h["category"] in hour_cats)
        if fact_hit or hour_total >= 30:
            hits += 1
            if fact_hit:
                evidence.append(f"They screen for {need}; you have it: [F{fact_hit['id']}] {fact_hit['text'][:80]}")
            else:
                evidence.append(f"They screen for {need}; your {hour_total:.0f} logged hours speak to it.")
        else:
            gaps.append(need)
    return hits, evidence, gaps


def scout_school(user: dict, school_id: str) -> dict:
    school = get_school(school_id)
    if not school:
        raise ValueError(f"unknown school: {school_id}")

    stat_band, stat_ev = _stat_distance(user, school)
    hits, mission_ev, gaps = _mission_fit(user["email"], school)

    in_state = bool(user.get("state")) and user["state"].upper() == school["state"]
    residency_note = ""
    verdict_shift = 0
    if school.get("in_state_preference") == "strong":
        if in_state:
            residency_note = "You're in-state, and this school heavily favors residents — that's a real edge."
            verdict_shift = 1
        else:
            residency_note = "This school heavily favors in-state applicants. Out-of-state, treat it as a long shot unless you have a genuine tie."
            verdict_shift = -1
    elif school.get("in_state_preference") == "moderate" and in_state:
        residency_note = "In-state helps here."
        verdict_shift = 1 if stat_band in ("near", "below") else 0

    base = {"above": 3, "near": 2, "below": 1, "far_below": 0, "unknown": 1}[stat_band]
    score = max(0, min(4, base + verdict_shift + (1 if hits >= 2 else 0)))
    verdict = ["far_reach", "reach", "target", "target", "likely"][score]
    if stat_band == "unknown":
        verdict = "incomplete"

    why = stat_ev + mission_ev
    if residency_note:
        why.append(residency_note)
    if school.get("note"):
        why.append(school["note"])

    if verdict == "incomplete":
        move = "Add your GPA (and MCAT when you have it) to your profile, then run this scout again."
    elif gaps:
        move = f"Close the mission gap: they look for {gaps[0]}, and your profile doesn't show it yet. One recurring commitment fixes that."
    elif stat_band in ("below", "far_below"):
        move = "Your experience story fits; the stats gap is the work. Protect the GPA and set an MCAT plan before adding anything new."
    else:
        move = "You fit their picture. Get specific: read their mission page and write one sentence on why THIS school — you'll need it for the secondary."

    return {
        "school": {k: school[k] for k in ("id", "name", "type", "state", "city", "mission_tags")},
        "verdict": verdict,           # likely | target | reach | far_reach | incomplete
        "why": why,                   # evidence bullets, fact-cited
        "gaps": gaps,
        "move": move,
        "data_note": load_schools()["data_note"],
    }


def rank_all_schools(user: dict, include_do: bool = True) -> list[dict]:
    """Lightweight list ordering for the Schools tab (not a Move)."""
    out = []
    for s in load_schools()["schools"]:
        if s["type"] == "DO" and not include_do:
            continue
        stat_band, _ = _stat_distance(user, s)
        in_state = bool(user.get("state")) and user["state"].upper() == s["state"]
        sort_key = {"above": 0, "near": 1, "below": 2, "far_below": 3, "unknown": 1}[stat_band]
        if in_state and s.get("in_state_preference") in ("strong", "moderate"):
            sort_key -= 1
        out.append({**{k: s[k] for k in ("id", "name", "type", "state", "city", "median_gpa", "median_mcat", "mission_tags")},
                    "in_state": in_state, "sort_key": sort_key})
    out.sort(key=lambda x: (x["sort_key"], x["name"]))
    for o in out:
        o.pop("sort_key", None)
    return out
