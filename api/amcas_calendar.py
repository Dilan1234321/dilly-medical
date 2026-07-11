"""AMCAS cycle calendar engine.

Timing is worth more than most paid consulting: submitting the primary in
the first two weeks of June materially improves outcomes because schools
review on rolling admissions. This module answers, for any date and target
cycle: what phase is the student in, and what is this week's move.

Cycle naming: the '2028 cycle' means applying in summer 2027 to matriculate
fall 2028. AMCAS opens early May, submissions open ~May 27-ish, verified
apps reach schools late June, secondaries June-Sept, interviews Aug-Mar,
decisions Oct onward.
"""
from __future__ import annotations

from datetime import date


PHASES = [
    # (phase_id, label, this-week move)
    ("foundation", "Foundation", "Log every clinical/volunteer hour the week it happens — fresh reflections become your essays."),
    ("mcat_runway", "MCAT runway", "Lock your MCAT date and build a 3-month study calendar around your course load."),
    ("pre_submission", "Application spring", "Draft your personal statement from your logged reflections and ask for letters NOW — professors are slowest in April."),
    ("submit_window", "Submit window", "Submit your AMCAS primary this week if it's ready. Rolling admissions means every week of delay costs you."),
    ("secondaries", "Secondary season", "Turn every secondary around within 14 days of receiving it. Pre-write the common prompts (why us, diversity, challenge)."),
    ("interviews", "Interview season", "Rehearse out loud: one MMI-style ethics prompt and your 'why medicine' story this week."),
    ("decisions", "Decision season", "Send one meaningful update letter to your top choice if you have real news to share."),
]


def application_calendar_year(target_cycle_year: int) -> int:
    """The calendar year the student actually applies (cycle year - 1)."""
    return target_cycle_year - 1


def phase_for(today: date, target_cycle_year: int | None) -> dict:
    """Return {phase, label, move, months_to_submission}."""
    if not target_cycle_year:
        return _as_dict("foundation", None)

    apply_year = application_calendar_year(target_cycle_year)
    submit_open = date(apply_year, 5, 28)   # approximate AMCAS submission open
    months_out = (submit_open.year - today.year) * 12 + (submit_open.month - today.month)

    if today >= date(apply_year + 1, 2, 1):
        return _as_dict("decisions", months_out)
    if today >= date(apply_year, 8, 15):
        return _as_dict("interviews", months_out)
    if today >= date(apply_year, 6, 25):
        return _as_dict("secondaries", months_out)
    if today >= date(apply_year, 5, 1):
        return _as_dict("submit_window", months_out)
    if today >= date(apply_year, 1, 1):
        return _as_dict("pre_submission", months_out)
    if months_out <= 18:
        return _as_dict("mcat_runway", months_out)
    return _as_dict("foundation", months_out)


def _as_dict(phase_id: str, months_to_submission: int | None) -> dict:
    for pid, label, move in PHASES:
        if pid == phase_id:
            return {
                "phase": pid,
                "label": label,
                "move": move,
                "months_to_submission": months_to_submission,
            }
    raise ValueError(f"unknown phase {phase_id}")
