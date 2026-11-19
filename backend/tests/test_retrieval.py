"""Retrieval, RRF and confidence tests (§7)."""
from __future__ import annotations

from app.db.models import Chunk
from app.retrieval.chunking import chunk_document, content_hash
from app.retrieval.evaluation import QUESTIONS, evaluate
from app.retrieval.hybrid import HybridRetriever, normalize_query


def test_chunking_overlap():
    text = "\n".join(f"Line {i} " + "word " * 30 for i in range(60))
    chunks = chunk_document("doc-1", text, "en")
    assert len(chunks) > 1
    assert all(c["content_hash"] == content_hash(c["content"]) for c in chunks)
    assert len(chunks[0]["content"].split()) <= 410


def test_content_hash_idempotent():
    assert content_hash("  hello   world ") == content_hash("hello world")


def test_normalize_query():
    n = normalize_query("Kal ka time kya hai?")
    assert "कल" in n and "समय" in n


def test_rrf_constant():
    from app.retrieval.hybrid import RRF_K as K
    assert K == 60


def test_retriever_grounding(db):
    r = HybridRetriever(prefer_real=False)
    chunks = db.query(Chunk).all()
    r.build(chunks)
    good = r.query("What is Dr. Mehta's consultation fee?")
    bad = r.query("What is the clinic's ISO certification code?")
    assert good.grounded is True
    assert bad.grounded is False
    assert len(good.chunks) <= 4
    assert all(c.rrf_score > 0 for c in good.chunks)


def test_evaluation_dataset_size():
    assert len(QUESTIONS) == 40
    assert sum(q["answerable"] for q in QUESTIONS) == 30
    assert sum(not q["answerable"] for q in QUESTIONS) == 10


def test_evaluation_metrics(db):
    r = HybridRetriever(prefer_real=False)
    r.build(db.query(Chunk).all())
    m = evaluate(r)
    assert 0 <= m.recall_at_4 <= 1
    assert m.groundedness >= 0.8
    assert m.unanswerable_rejection >= 0.8
