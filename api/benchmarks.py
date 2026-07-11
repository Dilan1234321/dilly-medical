"""Matriculant benchmarks used by the Readiness Read.

Sources: AAMC applicant/matriculant tables (public aggregates) plus
pre-health advising consensus bands for experience hours. Values are
approximate by design — they set honest expectation bands, not verdicts.
Update yearly when AAMC publishes new tables (see data_note in responses).
"""
from __future__ import annotations

# AAMC national aggregates (approximate, recent cycles).
MATRICULANT_GPA_AVG = 3.77
MATRICULANT_MCAT_AVG = 511.7
APPLICANT_GPA_AVG = 3.64
APPLICANT_MCAT_AVG = 506.3

DO_MATRICULANT_GPA_AVG = 3.61
DO_MATRICULANT_MCAT_AVG = 504.8

# Experience bands (advising consensus; hours by the time of application).
# band = (getting_started_below, on_track_at, strong_at)
HOUR_BANDS = {
    "clinical": (50, 150, 400),        # paid + volunteer clinical combined
    "shadowing": (15, 50, 100),
    "research": (0, 100, 400),         # 0 floor: not required for many mission fits
    "volunteering": (30, 100, 250),    # non-clinical service
    "leadership": (0, 50, 150),
}

DATA_NOTE = (
    "Benchmarks are approximate national aggregates (AAMC tables + advising "
    "consensus). They describe the field, not your ceiling. Verify school-"
    "specific numbers in MSAR before you finalize your list."
)


def band_label(value: float, band: tuple) -> str:
    """Map a value onto a benchmark band -> getting_started | on_track | strong."""
    low, mid, high = band
    if value >= high:
        return "strong"
    if value >= mid:
        return "on_track"
    if value > low:
        return "building"
    return "getting_started"
