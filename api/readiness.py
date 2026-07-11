"""The Readiness Read — 'if you applied today, here's your honest picture.'

Five dimensions: stats, clinical, shadowing, research_and_service, story.
Each dimension returns a BAND (never a numeric score), evidence that cites
real profile facts [F#] and hours entries [H#], and exactly one move.

Rule-based and deterministic; an optional LLM pass (llm.complete) can
rewrite the prose warmer, but the bands and evidence are always computed
here so they can never be hallucinated.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from . import benchmarks
from .amcas_calendar import phase_for
from .database import get_db


BANDS = ["getting_started", "building", "on_track", "strong", "unknown"]

_BAND_COPY = {
    "strong": "ahead of the field here",
    "on_track": "on track here",
    "building": "building — keep going",
    "getting_started": "this is your open lane",
    "unknown": "I don't know enough yet",
}


def _hours_by_category(email: str) -> dict:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, category, hours, org, role, occurred_on, reflection FROM hours_log WHERE email=?",
            (email,),
        ).fetchall()
    agg: dict[str, float] = {}
    entries = []
    for r in rows:
        agg[r["category"]] = agg.get(r["category"], 0.0) + (r["hours"] or 0.0)
        entries.append(dict(r))
    return {"totals": agg, "entries": entries}


def _facts(email: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, category, text, created_at FROM facts WHERE email=? AND archived=0 ORDER BY id",
            (email,),
        ).fetchall()
    return [dict(r) for r in rows]


def _cite_hours(entries: list[dict], categories: tuple, limit: int = 2) -> list[str]:
    cites = []
    for e in entries:
        if e["category"] in categories and len(cites) < limit:
            where = e["org"] or e["role"] or e["category"]
            cites.append(f"[H{e['id']}] {e['hours']:.0f}h {where}")
    return cites


def _cite_facts(facts: list[dict], categories: tuple, limit: int = 2) -> list[str]:
    cites = []
    for f in facts:
        if f["category"] in categories and len(cites) < limit:
            text = f["text"][:90]
            cites.append(f"[F{f['id']}] {text}")
    return cites


def _stats_dimension(user: dict) -> dict:
    gpa = user.get("gpa")
    mcat = user.get("mcat")
    evidence, moves = [], []

    if gpa is None and mcat is None:
        return {
            "dimension": "stats",
            "band": "unknown",
            "headline": "Add your GPA so I can read you against real matriculants.",
            "evidence": [],
            "move": "Add your cumulative GPA to your profile — it takes ten seconds and unlocks this whole read.",
        }

    band = "on_track"
    if gpa is not None:
        evidence.append(f"Your GPA is {gpa:.2f}; recent MD matriculants average about {benchmarks.MATRICULANT_GPA_AVG:.2f}.")
        if gpa >= benchmarks.MATRICULANT_GPA_AVG:
            band = "strong"
        elif gpa >= benchmarks.APPLICANT_GPA_AVG:
            band = "on_track"
        elif gpa >= 3.4:
            band = "building"
        else:
            band = "getting_started"
        trend = (user.get("gpa_trend") or "").strip()
        if trend == "rising" and band in ("building", "getting_started"):
            evidence.append("Your GPA trend is rising — schools weight the last two years heavily, so keep the slope.")
        elif trend == "falling":
            evidence.append("Your GPA trend is falling — that gets asked about, so have the honest story ready.")

    if mcat is not None:
        evidence.append(f"Your MCAT is {mcat}; matriculants average about {benchmarks.MATRICULANT_MCAT_AVG:.0f}.")
        if mcat >= 515:
            band = "strong" if band != "getting_started" else "building"
        elif mcat < 500:
            band = "getting_started"
            moves.append("Your MCAT is below the band where most MD schools screen. A well-planned retake is a real option — build a 3-month runway before you commit a date.")
    elif user.get("mcat_planned_month"):
        evidence.append(f"MCAT planned for {user['mcat_planned_month']} — your GPA carries the stats read until then.")
    else:
        moves.append("Pick a target MCAT month and work backwards — the date decides your whole prep calendar.")

    move = moves[0] if moves else (
        "Protect the GPA: your next semester matters more than any extracurricular this week."
        if band in ("building", "getting_started")
        else "Stats are doing their job. Spend your energy on hours and story this month."
    )
    return {
        "dimension": "stats",
        "band": band,
        "headline": f"Stats: {_BAND_COPY[band]}.",
        "evidence": evidence,
        "move": move,
    }


def _clinical_dimension(hours: dict, facts: list[dict]) -> dict:
    total = hours["totals"].get("clinical_paid", 0) + hours["totals"].get("clinical_volunteer", 0)
    band = benchmarks.band_label(total, benchmarks.HOUR_BANDS["clinical"])
    evidence = [f"You've logged {total:.0f} clinical hours; applicants typically show {benchmarks.HOUR_BANDS['clinical'][1]}-{benchmarks.HOUR_BANDS['clinical'][2]}+ by submission."]
    evidence += _cite_hours(hours["entries"], ("clinical_paid", "clinical_volunteer"))
    evidence += _cite_facts(facts, ("clinical",), 1)
    if total == 0:
        move = "Get one clinical foothold this month: scribe, CNA/PCT, EMT course, or a hospice volunteer shift. Paid counts."
    elif band in ("building", "getting_started"):
        move = "Add one recurring weekly clinical shift — 4 hours a week becomes 200 hours by application season."
    else:
        move = "Your clinical base is real. Now go deeper, not wider: more responsibility where you already are."
    return {"dimension": "clinical", "band": band, "headline": f"Clinical: {_BAND_COPY[band]}.", "evidence": evidence, "move": move}


def _shadowing_dimension(hours: dict, user: dict) -> dict:
    total = hours["totals"].get("shadowing", 0)
    band = benchmarks.band_label(total, benchmarks.HOUR_BANDS["shadowing"])
    evidence = [f"You've logged {total:.0f} shadowing hours; {benchmarks.HOUR_BANDS['shadowing'][1]}+ across 2-3 specialties is the usual bar."]
    evidence += _cite_hours(hours["entries"], ("shadowing",))
    if user.get("include_do") and total > 0:
        evidence.append("If DO schools are on your list, make sure at least one shadowed physician is a DO — they check.")
    move = (
        "Email two physicians this week asking for a half-day. Your own doctors are the warmest door."
        if band in ("building", "getting_started")
        else "Shadowing is covered. One primary-care half-day a semester keeps it current."
    )
    return {"dimension": "shadowing", "band": band, "headline": f"Shadowing: {_BAND_COPY[band]}.", "evidence": evidence, "move": move}


def _research_service_dimension(hours: dict, facts: list[dict]) -> dict:
    research = hours["totals"].get("research", 0)
    service = hours["totals"].get("volunteering", 0) + hours["totals"].get("leadership", 0)
    r_band = benchmarks.band_label(research, benchmarks.HOUR_BANDS["research"])
    s_band = benchmarks.band_label(service, benchmarks.HOUR_BANDS["volunteering"])
    order = {b: i for i, b in enumerate(["getting_started", "building", "on_track", "strong"])}
    band = min(r_band, s_band, key=lambda b: order[b])

    evidence = [
        f"Research: {research:.0f}h logged. Service and leadership: {service:.0f}h logged.",
    ]
    evidence += _cite_hours(hours["entries"], ("research",), 1)
    evidence += _cite_hours(hours["entries"], ("volunteering", "leadership"), 1)
    evidence += _cite_facts(facts, ("research", "service", "leadership"), 2)

    if s_band in ("getting_started", "building"):
        move = "Pick ONE service commitment you'd do even if med school didn't exist, and show up weekly. Depth beats variety."
    elif r_band in ("getting_started", "building"):
        move = "Email three PIs whose work you can say one real sentence about. Research opens research-heavy school lists."
    else:
        move = "Both engines are running. Aim for an output: a poster, a leadership role, a project you own."
    return {"dimension": "research_and_service", "band": band, "headline": f"Research and service: {_BAND_COPY[band]}.", "evidence": evidence, "move": move}


def _story_dimension(hours: dict, facts: list[dict]) -> dict:
    reflections = [e for e in hours["entries"] if (e.get("reflection") or "").strip()]
    life_facts = [f for f in facts if f["category"] in ("life", "award", "letter")]
    n = len(reflections)
    if n >= 12:
        band = "strong"
    elif n >= 5:
        band = "on_track"
    elif n >= 1:
        band = "building"
    else:
        band = "getting_started"
    evidence = [f"You've captured {n} reflections in your hours log — these are the raw material of your personal statement and interviews."]
    if reflections:
        newest = reflections[-1]
        evidence.append(f"[H{newest['id']}] Most recent: \"{(newest['reflection'] or '')[:80]}\"")
    if life_facts:
        evidence.append(f"[F{life_facts[0]['id']}] {life_facts[0]['text'][:90]}")
    move = (
        "After your next shift, answer one question into the mic: what stuck with you today? Thirty seconds now saves you a blank page in application spring."
        if band in ("getting_started", "building")
        else "Your anecdote bank is growing. Tag the three moments that still make you feel something — those are personal statement candidates."
    )
    return {"dimension": "story", "band": band, "headline": f"Story: {_BAND_COPY[band]}.", "evidence": evidence, "move": move}


def run_readiness_read(user: dict) -> dict:
    """Compute the full read. Deterministic; safe without an LLM."""
    email = user["email"]
    hours = _hours_by_category(email)
    facts = _facts(email)

    dims = [
        _stats_dimension(user),
        _clinical_dimension(hours, facts),
        _shadowing_dimension(hours, user),
        _research_service_dimension(hours, facts),
        _story_dimension(hours, facts),
    ]

    order = {b: i for i, b in enumerate(["getting_started", "building", "on_track", "strong", "unknown"])}
    weakest = min((d for d in dims if d["band"] != "unknown"), key=lambda d: order[d["band"]], default=dims[0])

    phase = phase_for(date.today(), user.get("target_cycle_year"))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "dimensions": dims,
        "your_open_lane": weakest["dimension"],
        "this_week": weakest["move"],
        "data_note": benchmarks.DATA_NOTE,
    }
