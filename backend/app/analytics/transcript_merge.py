"""Merge caller and agent channel transcripts into one chronological view.

Timestamps come from batch STT and are estimated; ordering is approximate and
is labelled as such in the UI and in the stored JSON.
"""
from __future__ import annotations

from typing import Any


def merge_transcripts(caller: dict, agent: dict) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    for speaker, data in (("caller", caller), ("agent", agent)):
        for seg in data.get("segments", []):
            turns.append({
                "speaker": speaker,
                "start": seg.get("start", 0),
                "end": seg.get("end", 0),
                "text": seg.get("text", ""),
                "timing_quality": "estimated",
            })
    turns.sort(key=lambda t: t["start"])
    for i, turn in enumerate(turns):
        turn["idx"] = i
    return turns


def render(turns: list[dict[str, Any]]) -> str:
    return "\n".join(f"[{t['idx']:02d}] {t['speaker']}: {t['text']}" for t in turns)
