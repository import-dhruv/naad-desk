"""Call history, details and analysis endpoints (§14)."""
from __future__ import annotations

import json
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..analytics.pipeline import analyze_call
from ..db import models as m
from ..db.database import get_db
from ..schemas.calls import CallCreate, CallSummary

router = APIRouter()


def _utc(value):
    """Normalise DB datetimes (naive on some drivers) to aware UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _duration(call: m.Call) -> float | None:
    if not call.ended_at or not call.started_at:
        return None
    return (_utc(call.ended_at) - _utc(call.started_at)).total_seconds()


@router.post("/api/calls", response_model=dict)
def create_call(body: CallCreate, db: Session = Depends(get_db)):
    import uuid
    call_id = f"call-{uuid.uuid4().hex[:12]}"
    db.add(m.Call(id=call_id, language=body.language,
                  prompt_version="v1.0", kb_version="kb-v1",
                  recording_disclosure=body.disclosure_ack))
    db.commit()
    return {"id": call_id, "language": body.language}


@router.get("/api/calls", response_model=list[CallSummary])
def list_calls(db: Session = Depends(get_db)):
    calls = db.query(m.Call).order_by(m.Call.started_at.desc()).all()
    return [CallSummary(
        id=c.id, started_at=c.started_at, ended_at=c.ended_at, language=c.language,
        outcome=c.outcome, qa_score=c.qa_score, cost_paise=c.cost_paise,
        duration_seconds=_duration(c),
    ) for c in calls]


@router.get("/api/calls/{call_id}")
def get_call(call_id: str, db: Session = Depends(get_db)):
    call = db.get(m.Call, call_id)
    if call is None:
        raise HTTPException(404, "call not found")
    turns = db.query(m.Turn).filter(m.Turn.call_id == call_id).order_by(m.Turn.idx).all()
    tools = (db.query(m.ToolCall).join(m.Turn).filter(m.Turn.call_id == call_id).all())
    retrievals = (db.query(m.Retrieval).join(m.Turn).filter(m.Turn.call_id == call_id).all())
    analytics = db.get(m.Analytics, call_id)
    api_calls = db.query(m.ApiCall).filter(m.ApiCall.call_id == call_id).all()
    return {
        "id": call.id, "started_at": call.started_at.isoformat(),
        "ended_at": call.ended_at.isoformat() if call.ended_at else None,
        "language": call.language, "outcome": call.outcome,
        "qa_score": call.qa_score, "cost_paise": call.cost_paise,
        "duration_seconds": _duration(call),
        "turns": [{
            "idx": t.idx, "speaker": t.speaker, "text": t.text, "language": t.language,
            "timings": {k: getattr(t, k) for k in (
                "t_client_end_speech", "t_engine_endpoint", "t_transcript", "t_retrieval",
                "t_plan", "t_tool", "t_first_say", "t_first_audio", "t_first_played",
                "t_turn_complete") if getattr(t, k) is not None},
        } for t in turns],
        "tool_calls": [{"name": t.name, "args": json.loads(t.args_json),
                        "result": json.loads(t.result_json),
                        "execution_time_ms": t.execution_time_ms} for t in tools],
        "retrievals": [{"chunk_ids": json.loads(r.chunk_ids), "scores": json.loads(r.scores),
                        "confidence": r.confidence,
                        "execution_time_ms": r.execution_time_ms} for r in retrievals],
        "analytics": ({
            "caller_transcript": analytics.caller_transcript,
            "agent_transcript": analytics.agent_transcript,
            "merged_transcript": json.loads(analytics.merged_transcript or "[]"),
            "extraction": json.loads(analytics.extraction_json or "{}"),
            "qa": json.loads(analytics.qa_json or "{}"),
            "summary": analytics.summary,
        } if analytics else None),
        "api_calls": [{"endpoint": a.endpoint, "status": a.status,
                       "latency_ms": a.latency_ms, "cost_paise": a.cost_paise,
                       "headers": json.loads(a.headers_json or "{}")} for a in api_calls],
        "recordings": {
            "caller": f"/api/calls/{call_id}/recording/caller",
            "agent": f"/api/calls/{call_id}/recording/agent",
        },
    }


@router.post("/api/calls/{call_id}/analyze")
async def analyze(call_id: str, db: Session = Depends(get_db)):
    if db.get(m.Call, call_id) is None:
        raise HTTPException(404, "call not found")
    result = await analyze_call(db, call_id)
    if result.get("error") == "no_recordings":
        raise HTTPException(422, "no recordings available for this call")
    return result


@router.get("/api/calls/{call_id}/recording/{channel}")
def recording(call_id: str, channel: str):
    import os
    from pathlib import Path

    from fastapi.responses import FileResponse

    from ..config import ROOT, settings
    if channel not in ("caller", "agent"):
        raise HTTPException(400, "invalid channel")
    base = (Path(os.getenv("RECORDINGS_DIR", "/tmp/naad-recordings"))
            if settings.is_vercel else ROOT / "recordings")
    path = base / call_id / f"{channel}.wav"
    if not path.exists():
        raise HTTPException(404, "recording not found")
    return FileResponse(path, media_type="audio/wav")
