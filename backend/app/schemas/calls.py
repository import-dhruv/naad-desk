"""Schemas for call REST endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CallCreate(BaseModel):
    language: str = "hi"
    voice: str | None = None
    disclosure_ack: bool = True


class CallSummary(BaseModel):
    id: str
    started_at: datetime
    ended_at: datetime | None
    language: str
    outcome: str
    qa_score: float | None
    cost_paise: int
    duration_seconds: float | None = None


class TokenResponse(BaseModel):
    call_id: str
    session_token: str
    expires_in: int
    ws_url: str
