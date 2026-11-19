"""Idempotent document ingestion for Markdown (and PDF when available) (§7.1)."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..config import ROOT
from ..db.models import Chunk, Document
from .chunking import chunk_document, content_hash, normalize_text
from .hybrid import HybridRetriever


def _detect_language(path: Path, text: str) -> str:
    parts = path.parts
    for lang, marker in (("gu", "gu"), ("hi", "hi"), ("en", "en")):
        if marker in parts:
            return lang
    dev = sum("\u0900" <= c <= "\u097f" for c in text)
    guj = sum("\u0a80" <= c <= "\u0aff" for c in text)
    if guj > dev and guj > 20:
        return "gu"
    if dev > 20:
        return "hi"
    return "en"


def _extract(path: Path) -> str:
    if path.suffix.lower() == ".md":
        return normalize_text(path.read_text(encoding="utf-8"))
    if path.suffix.lower() == ".pdf":
        try:
            import pdfplumber  # type: ignore
            with pdfplumber.open(path) as pdf:
                return normalize_text("\n".join(p.extract_text() or "" for p in pdf.pages))
        except Exception as exc:
            raise RuntimeError(f"PDF extraction unavailable: {exc}") from exc
    raise ValueError(f"Unsupported document type: {path.suffix}")


def ingest_directory(db: Session, directory: Path | None = None,
                     retriever: HybridRetriever | None = None) -> dict:
    directory = directory or (ROOT / "knowledge")
    files = sorted([*directory.rglob("*.md"), *directory.rglob("*.pdf")])
    stats = {"files": len(files), "ingested": 0, "unchanged": 0, "chunks": 0,
             "total_chars": 0, "errors": []}
    for path in files:
        try:
            text = _extract(path)
            ch = content_hash(text)
            doc_id = str(path.relative_to(directory))
            existing = db.get(Document, doc_id)
            if existing and existing.content_hash == ch:
                stats["unchanged"] += 1
                stats["total_chars"] += existing.char_count
                continue
            if existing:
                db.execute(delete(Chunk).where(Chunk.document_id == doc_id))
            language = _detect_language(path, text)
            chunks = chunk_document(doc_id, text, language)
            title = path.stem.replace("_", " ").title()
            if existing:
                existing.content_hash = ch
                existing.char_count = len(text)
                existing.chunk_count = len(chunks)
                existing.language = language
                existing.source = str(path.relative_to(directory))
                existing.title = title
                existing.status = "indexed"
            else:
                db.add(Document(id=doc_id, source=str(path.relative_to(directory)),
                                language=language, title=title, content_hash=ch,
                                char_count=len(text), chunk_count=len(chunks), status="indexed"))
            for c in chunks:
                db.merge(Chunk(**c))
            db.commit()
            stats["ingested"] += 1
            stats["chunks"] += len(chunks)
            stats["total_chars"] += len(text)
        except Exception as exc:
            db.rollback()
            stats["errors"].append(f"{path.name}: {exc}")

    if retriever is not None:
        retriever.build_from_db(db)
    return stats


def get_documents(db: Session) -> list[dict]:
    return [
        {
            "id": d.id, "source": d.source, "language": d.language, "title": d.title,
            "char_count": d.char_count, "chunk_count": d.chunk_count,
            "indexed_at": d.indexed_at.isoformat() if d.indexed_at else None,
            "status": d.status,
        }
        for d in db.scalars(select(Document)).all()
    ]
