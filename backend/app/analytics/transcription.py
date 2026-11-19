"""Dual-channel batch transcription (§10.2).

The documented batch STT endpoint does not diarize and marks timestamps as
estimated. We preserve that label everywhere; no word-level alignment is claimed.
"""
from __future__ import annotations

import io
import wave
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from ..gateway.oogam_client import oogam

STT_CODES = {"hi": "HIN", "gu": "GUJ", "en-in": "ENG"}


def _to_16k_wav(audio: bytes) -> bytes:
    """Batch STT expects 16 kHz; resample and keep payload modest."""
    try:
        samples, rate = sf.read(io.BytesIO(audio), dtype="float32", always_2d=False)
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        if rate != 16000:
            samples = resample_poly(samples, 16000, rate)
        pcm = np.clip(samples * 32767, -32768, 32767).astype("<i2")
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(pcm.tobytes())
        return buf.getvalue()
    except Exception:
        return audio


async def transcribe_channel(path: Path, language: str, call_id: str,
                             blob_reference: str | None = None) -> dict:
    audio: bytes | None = None
    if blob_reference:
        from ..gateway.blob_store import download_recording
        audio = await download_recording(blob_reference)
    if audio is None and path.exists():
        audio = path.read_bytes()
    if audio is None:
        return {"text": "", "segments": [], "estimated_timestamps": True, "missing": True}
    result = await oogam.stt(_to_16k_wav(audio), STT_CODES.get(language, "HIN"),
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
