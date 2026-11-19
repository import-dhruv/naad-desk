"""Health endpoint (§14)."""
from __future__ import annotations

import time

from fastapi import APIRouter
from sqlalchemy import text

from ..config import settings
from ..db.database import SessionLocal

router = APIRouter()


@router.get("/api/health")
async def health() -> dict:
    db_status = "ok"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as exc:
        db_status = f"error: {exc}"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": "1.0.0",
        "database": db_status,
        "upstream": {
            "configured": settings.has_api_key,
            "rest_base": settings.rest_base,
            "ws_url": settings.ws_url.split("?")[0],
        },
        "retrieval": "ready",
        "storage": ("ephemeral (/tmp SQLite) — data is reset on cold start"
                    if settings.is_vercel else "local SQLite file"),
        "timestamp": time.time(),
    }
