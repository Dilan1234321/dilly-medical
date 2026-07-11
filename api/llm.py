"""Optional Anthropic client. Every caller MUST have a deterministic fallback.

Same model + habits as career Dilly (Claude Haiku, cost-conscious, one call
per Move). If no ANTHROPIC_API_KEY is configured, complete() returns None
and callers use their rule-based path — the product works fully offline.
"""
from __future__ import annotations

from .config import config


def is_llm_available() -> bool:
    return bool(config.anthropic_api_key)


def complete(system: str, user: str, max_tokens: int = 1200) -> str | None:
    """One-shot completion. Returns None on any failure — never raises."""
    if not is_llm_available():
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        msg = client.messages.create(
            model=config.llm_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts = [b.text for b in msg.content if getattr(b, "type", "") == "text"]
        return "\n".join(parts).strip() or None
    except Exception:
        return None


NO_FABRICATION_RULES = """HARD RULES (violating any of these is a critical failure):
- NEVER invent a fact, metric, patient story, organization, course, score, or skill.
- Every claim must trace to a numbered profile fact [F#] or hours-log entry [H#] you were given.
- If the evidence is thin, say less. A short honest read beats a padded one.
- The student is an UNDERGRADUATE applying to medical school. Never mention MBA/PhD/postdoc paths.
- Never output a numeric score or percentage chance of admission.
- No markdown emphasis: no bold, no italics, no headers. Plain sentences only.
- Never recommend Caribbean medical schools.
- End with exactly one concrete next action the student can take this week."""
