"""Dilly Medical config — env-driven, safe defaults for local dev."""
from __future__ import annotations

import os


class Config:
    # SQLite file path. Self-contained by default; point at a mounted volume in prod.
    db_path: str = os.environ.get(
        "DILLY_MED_DB",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "dilly_medical.db"),
    )

    # Dev mode: /auth/send-code returns the code in the response (no email provider yet).
    dev_mode: bool = os.environ.get("DILLY_MED_DEV", "1") == "1"

    # LLM (optional). All reads have deterministic fallbacks so the API works without a key.
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    llm_model: str = os.environ.get("DILLY_MED_LLM_MODEL", "claude-haiku-4-5-20251001")

    cors_origins: list = (
        os.environ.get("DILLY_MED_CORS", "*").split(",")
        if os.environ.get("DILLY_MED_CORS")
        else ["*"]
    )

    # Gated diagnostic endpoints (mirror career Dilly's X-Cron-Secret habit).
    cron_secret: str = os.environ.get("CRON_SECRET", "")


config = Config()
