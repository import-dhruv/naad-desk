"""Dual-channel batch transcription (§10.2).

The documented batch STT endpoint does not diarize and marks timestamps as
estimated. We preserve that label everywhere; no word-level alignment is claimed.
"""
from __future__ import annotations

from pathlib import Path

from ..gateway.oogam_client import oogam

STT_CODES = {"hi": "HIN", "gu": "GUJ", "en-in": "ENG"}


async def transcribe_channel(path: Path, language: str, call_id: str) -> dict:
    if not path.exists():
        return {"text": "", "segments": [], "estimated_timestamps": True, "missing": True}
    result = await oogam.stt(path.read_bytes(), STT_CODES.get(language, "HIN"),
                             verbose=True, call_id=call_id)
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": seg.get("start", 0), "end": seg.get("end", 0),
            "text": seg.get("text", ""), "timing": "estimated",
        })
    return {
        "text": result.get("text", ""),
        "language": result.get("language", language),
        "duration": result.get("duration", 0),
        "segments": segments,
        "estimated_timestamps": bool(result.get("timestampsEstimated", True)),
        "raw": result,
    }
