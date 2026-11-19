"""Fast local smoke test: DB seed -> KB ingest -> retrieval -> evaluation.

Run: .venv/bin/python scripts/smoke_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.database import SessionLocal, init_db  # noqa: E402
from app.db.seed import seed  # noqa: E402
from app.retrieval.evaluation import evaluate  # noqa: E402
from app.retrieval.hybrid import HybridRetriever  # noqa: E402
from app.retrieval.ingestion import ingest_directory  # noqa: E402


def main() -> None:
    init_db()
    print("seed:", seed())
    db = SessionLocal()
    try:
        stats = ingest_directory(db, ROOT / "knowledge", retriever=None)
        print("ingest:", stats)
        retriever = HybridRetriever(prefer_real=False)
        retriever.build_from_db(db)
        print("retrieval backend:", retriever.embedder.backend, "| chunks:", len(retriever.chunks))

        for q in ["What is Dr. Mehta's consultation fee?", "kal ka time kya hai?",
                  "ડૉક્ટર પટેલની ફી", "clinic ka license number kya hai?"]:
            r = retriever.query(q)
            print(f"\nQ: {q}\n  norm={r.normalized_query}\n  conf={r.confidence} grounded={r.grounded}")
            for c in r.chunks[:2]:
                print(f"   - {c.chunk_id} rrf={c.rrf_score:.4f} :: {c.content[:90]}")

        m = evaluate(retriever)
        print("\nretrieval metrics:", {
            "recall@4": m.recall_at_4, "groundedness": m.groundedness,
            "unanswerable_rejection": m.unanswerable_rejection,
            "hinglish_delta": m.hinglish_recall_delta,
        })
    finally:
        db.close()


if __name__ == "__main__":
    main()
