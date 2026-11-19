"""Sentence-level response composition for streaming `say` (§6.3)."""
from __future__ import annotations

import re

MAX_CHARS = 500
PREFER_CHARS = 180

BOUNDARY = re.compile(r"(?<=[.!?।])\s+")


def split_sentences(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    sentences = [s.strip() for s in BOUNDARY.split(text) if s.strip()]
    # Handle danda without trailing space (common in Devanagari/Gujarati).
    refined: list[str] = []
    for s in sentences:
        if len(s) > PREFER_CHARS and "।" in s:
            parts = [p.strip() for p in s.split("।") if p.strip()]
            refined.extend(p + "।" for p in parts)
        else:
            refined.append(s)
    return refined or [text]


def make_chunks(text: str, max_chars: int = MAX_CHARS, prefer: int = PREFER_CHARS) -> list[str]:
    """Group sentences into chunks ending at a sentence boundary, <500 chars."""
    sentences = split_sentences(text)
    chunks: list[str] = []
    buf = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            # Hard-split pathologically long sentence at word boundary.
            words = sentence.split()
            current = ""
            for w in words:
                if len(current) + len(w) + 1 > max_chars and current:
                    chunks.append(current.strip())
                    current = ""
                current += (" " if current else "") + w
            if current:
                chunks.append(current.strip())
            continue
        if buf and len(buf) + len(sentence) + 1 > prefer:
            chunks.append(buf.strip())
            buf = ""
        buf = (buf + " " + sentence).strip()
    if buf:
        chunks.append(buf.strip())
    return chunks


def streaming_say_sequence(chunks: list[str]) -> list[dict]:
    """Convert chunks into `say` frames: all final:false, last final:true."""
    frames = []
    for i, chunk in enumerate(chunks):
        frames.append({"type": "say", "text": chunk[:MAX_CHARS], "final": i == len(chunks) - 1})
    return frames
