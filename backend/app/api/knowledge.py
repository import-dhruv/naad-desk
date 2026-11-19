"""Knowledge-base inspection and ingestion endpoints (§14)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..gateway.websocket import set_retriever
from ..retrieval.hybrid import HybridRetriever
from ..retrieval.ingestion import get_documents, ingest_directory

router = APIRouter()


class IngestRequest(BaseModel):
    directory: str | None = None


@router.post("/api/kb/ingest")
def ingest(body: IngestRequest | None = None, db: Session = Depends(get_db)):
    from pathlib import Path

    from ..config import ROOT
    directory = Path(body.directory) if body and body.directory else ROOT / "knowledge"
    retriever = HybridRetriever()
    stats = ingest_directory(db, directory, retriever)
    set_retriever(retriever)
    return stats


@router.get("/api/kb/documents")
def documents(db: Session = Depends(get_db)):
    return get_documents(db)
