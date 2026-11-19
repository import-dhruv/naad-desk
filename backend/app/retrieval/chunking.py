"""Text normalization and heading-aware chunking (§7.1)."""
from __future__ import annotations

import hashlib
import re
import unicodedata

CHUNK_TARGET_WORDS = 400
CHUNK_MIN_WORDS = 300
CHUNK_OVERLAP_WORDS = 50


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def split_markdown(text: str) -> list[tuple[str, str]]:
    """Split on markdown headings, keeping the heading as section metadata."""
    text = normalize_text(text)
    parts: list[tuple[str, str]] = []
    section = "Introduction"
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            if "".join(buf).strip():
                parts.append((section, "\n".join(buf).strip()))
            section = m.group(2).strip()
            buf = []
        else:
            buf.append(line)
    if "".join(buf).strip():
        parts.append((section, "\n".join(buf).strip()))
    return parts or [(section, text)]


def _words(text: str) -> list[str]:
    return text.split()


def chunk_section(section: str, text: str, doc_id: str, language: str,
                  target: int = CHUNK_TARGET_WORDS, overlap: int = CHUNK_OVERLAP_WORDS):
    words = _words(text)
    if len(words) <= target:
        yield {
            "id": f"{doc_id}::{hashlib.sha1((section + text).encode()).hexdigest()[:12]}",
            "document_id": doc_id, "section": section, "language": language,
            "content": text, "content_hash": content_hash(text), "idx": 0,
        }
        return
    start = 0
    idx = 0
    while start < len(words):
        end = min(start + target, len(words))
        piece = " ".join(words[start:end])
        yield {
            "id": f"{doc_id}::{idx:04d}",
            "document_id": doc_id, "section": section, "language": language,
            "content": piece, "content_hash": content_hash(piece), "idx": idx,
        }
        idx += 1
        if end >= len(words):
            break
        start = max(end - overlap, start + 1)


def chunk_document(doc_id: str, text: str, language: str):
    chunks = []
    for section, body in split_markdown(text):
        chunks.extend(chunk_section(section, body, doc_id, language))
    return chunks
