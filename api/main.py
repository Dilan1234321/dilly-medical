"""Dilly Medical API.

Run locally:
    cd dilly-medical && pip install -r api/requirements.txt
    uvicorn api.main:app --reload --port 8100
"""
from __future__ import annotations

import secrets
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from .config import config
from .database import init_db
from .routers import auth, brief, craft, cron, hours, interview, misc, opportunities, profile, readiness, schools, secondaries

app = FastAPI(
    title="Dilly Medical API",
    description="Med-school admissions coach for undergraduates: hours ledger, "
                "Readiness Read, School Scout, Craft, gap-matched opportunities.",
    version="0.2.0",
    openapi_tags=[
        {"name": "auth", "description": "Email + code auth, sessions"},
        {"name": "profile", "description": "Profile, facts, plan items"},
        {"name": "hours", "description": "Hours ledger + voice reflections + W&A export (always free)"},
        {"name": "readiness", "description": "Readiness Read (Move)"},
        {"name": "schools", "description": "School list + School Scout (Move)"},
        {"name": "opportunities", "description": "Gap-matched opportunity feed (static + live crawler)"},
        {"name": "craft", "description": "Essay/W&A drafting from real facts only (Move)"},
        {"name": "secondaries", "description": "Secondary essay prompts + Craft (Move)"},
        {"name": "interview", "description": "MMI + interview practice with AI feedback (Move)"},
        {"name": "brief", "description": "Cycle-aware weekly brief (free)"},
        {"name": "billing", "description": "Plan management (Stripe pending)"},
        {"name": "moves", "description": "Moves usage"},
        {"name": "cron", "description": "Scheduled crawler refresh"},
        {"name": "health", "description": "Health check"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Same observability habit as career Dilly: request_id, duration, no PII."""
    request_id = request.headers.get("X-Request-ID") or secrets.token_hex(8)
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000)
    path = request.url.path
    if not path.startswith("/health"):
        print(f"[MED] {request_id} {request.method} {path} {response.status_code} {duration_ms}ms", flush=True)
    response.headers["X-Request-ID"] = request_id
    return response


@app.on_event("startup")
def startup():
    init_db()
    # Warm the opportunity crawler on boot (non-blocking best-effort in dev).
    if config.dev_mode:
        try:
            from .crawler.opportunities import run_all_crawlers
            run_all_crawlers()
        except Exception as e:
            print(f"[MED] startup crawler skipped: {e}", flush=True)


app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(hours.router)
app.include_router(readiness.router)
app.include_router(schools.router)
app.include_router(opportunities.router)
app.include_router(craft.router)
app.include_router(secondaries.router)
app.include_router(interview.router)
app.include_router(brief.router)
app.include_router(misc.router)
app.include_router(cron.router)
