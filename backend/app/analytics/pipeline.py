"""Post-call analytics orchestration (§10)."""
from __future__ import annotations

import json
import os
from pathlib import Path

from sqlalchemy.orm import Session

from ..config import ROOT, settings
from ..db.models import Analytics, Call, Doctor, Slot, Turn
from ..db.models import Retrieval as RetrievalRow
from ..logging_util import log
from .extraction import extract
from .qa_scoring import score_call
from .summarization import build_summary
from .transcript_merge import merge_transcripts, render
from .transcription import transcribe_channel

RECORDINGS = (
    Path(os.getenv("RECORDINGS_DIR", "/tmp/naad-recordings"))
    if settings.is_vercel else ROOT / "recordings"
)


async def analyze_call(db: Session, call_id: str) -> dict:
    call = db.get(Call, call_id)
    if call is None:
        return {"error": "call not found"}

    if not ((RECORDINGS / call_id / "caller.wav").exists()
            and (RECORDINGS / call_id / "agent.wav").exists()):
        log.info("analysis_skipped_no_recordings", extra={"call_id": call_id})
        return {"error": "no_recordings", "call_id": call_id,
                "qa": None, "summary": "", "merged_turns": []}

    caller = await transcribe_channel(RECORDINGS / call_id / "caller.wav", call.language, call_id)
    agent = await transcribe_channel(RECORDINGS / call_id / "agent.wav", call.language, call_id)
    merged_turns = merge_transcripts(caller, agent)
    merged_text = render(merged_turns)

    extraction_model = await extract(merged_text or call_id, call_id)
    extraction = extraction_model.model_dump()

    turns = db.query(Turn).filter(Turn.call_id == call_id).order_by(Turn.idx).all()
    agent_text = " ".join(t.text for t in turns if t.speaker == "agent") or agent.get("text", "")
    retrievals = db.query(RetrievalRow).join(Turn).filter(Turn.call_id == call_id).all()
    confs = [r.confidence for r in retrievals]
    latencies = [t.t_turn_complete for t in turns if t.t_turn_complete]

    fees = {str(d.fee_paise // 100) for d in db.query(Doctor).all()}
    slot_minutes = {str(s.start_ts.minute) for s in db.query(Slot).limit(500).all()}
    known = fees | slot_minutes | {"112"}
    qa = score_call(extraction, merged_text, agent_text, confs, latencies, known,
                    extraction.get("safety_events", []))
    summary = build_summary(extraction, call.language)

    existing = db.get(Analytics, call_id)
    data = dict(
        caller_transcript=caller.get("text", ""),
        agent_transcript=agent.get("text", ""),
        merged_transcript=json.dumps(merged_turns, ensure_ascii=False),
        extraction_json=json.dumps(extraction, ensure_ascii=False),
        qa_json=json.dumps(qa, ensure_ascii=False),
        summary=summary,
    )
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
    else:
        db.add(Analytics(call_id=call_id, **data))
    call.qa_score = qa["total"]
    call.outcome = "analyzed"
    db.commit()
    log.info("call_analyzed", extra={"call_id": call_id, "qa_score": qa["total"]})
    return {"call_id": call_id, "qa": qa, "summary": summary,
            "extraction": extraction, "merged_turns": merged_turns}
