"""Cron + admin endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from ..config import config
from ..crawler.opportunities import run_all_crawlers

router = APIRouter(tags=["cron"])


def _require_cron(secret: str = Header(default="", alias="X-Cron-Secret")):
    if config.cron_secret and secret != config.cron_secret:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN"})


@router.post("/cron/refresh-opportunities")
def refresh_opportunities(x_cron_secret: str = Header(default="", alias="X-Cron-Secret")):
    """Refresh live_opportunities from external sources. GitHub Action or Railway cron."""
    if config.cron_secret:
        _require_cron(x_cron_secret)
    return run_all_crawlers()
