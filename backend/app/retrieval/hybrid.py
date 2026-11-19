"""Hybrid retrieval: BM25 + dense embeddings fused with Reciprocal Rank Fusion,
with confidence gating and Hinglish query normalisation (§7.2–7.4)."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import numpy as np
from sqlalchemy.orm import Session

from ..config import settings
from ..db.models import Chunk
from .bm25 import BM25Index
from .embeddings import DenseEmbedder

RRF_K = 60

# Function words ignored when deciding whether the KB actually contains an
# answer. Kept deliberately small so distinctive content words drive grounding.
STOP_TOKENS = {
    "the", "a", "an", "is", "are", "of", "to", "for", "and", "in", "on", "at",
    "what", "which", "who", "when", "how", "do", "does", "did", "i", "you",
    "my", "your", "it", "this", "that", "be", "can", "should", "would", "have",
    "hai", "ka", "ki", "ke", "kya", "क्या", "है", "का", "की", "के", "में", "और",
    "क्लिनिक", "clinic", "શું", "છે", "કા", "ક્લિનિક", "અને", "માટે",
    "much", "many", "long", "there", "where", "whose", "charge",
    "कितनी", "कितना", "क्यों", "कैसे", "કેટલી", "ક્યાં", "આજે", "શું",
    "for", "about", "please", "tell", "want", "need", "get", "have",
    "problems", "करूँ", "करने", "करना", "लिए", "कौन-से", "कौन-सा", "कौन-कौन",
    "तरीके", "हैं", "અને", "છે", "ક્યાં", "કેટલી",
}

# Surface-form equivalence groups for grounding coverage. A concept is covered
# if any member of its group appears anywhere in the corpus. This is a query
# expansion heuristic, not a learned semantic model (see decisions.md D-06).
SYNONYM_GROUPS: list[set[str]] = [
    {"fee", "fees", "शुल्क", "फी", "ફી", "charge", "price", "रुपये", "રૂપિયા"},
    {"open", "खुला", "ખુલ્લું", "band", "बंद", "closed"},
    {"sunday", "सोमवार", "रविवार", "રવિવાર", "रवि"},
    {"available", "उपलब्ध", "ઉપલબ્ધ", "availability"},
    {"doctor", "डॉक्टर", "ડૉક્ટર", "dr"},
    {"human", "मानव", "માનવ", "handoff", "एजेंट", "એજન્ટ"},
    {"emergency", "आपदा", "આપત્તિ", "112"},
    {"parking", "पार्किंग", "પાર્કિંગ"},
    {"insurance", "बीमा", "વીમો", "વીમા"},
    {"cancel", "रद्द", "રદ"},
    {"reschedule", "बदल", "બદલ"},
    {"mehta", "मेहता", "મેહતા"},
    {"patel", "पटेल", "પટેલ", "પટેલની"},
    {"shah", "शाह", "શાહ"},
    {"rao", "राव", "રાવ"},
]

# Romanised -> native-script canonical terms. Applied to queries only; the KB
# intentionally contains both native script and English terms.
HINGLISH_MAP = {
    "kal": "कल", "aaj": "आज", "parso": "परसों",
    "kya": "क्या", "kaise": "कैसे", "kitna": "कितना", "kab": "कब",
    "doctor": "डॉक्टर", "doctors": "डॉक्टर", "clinic": "क्लिनिक",
    "appointment": "अपॉइंटमेंट", "appointments": "अपॉइंटमेंट",
    "fee": "शुल्क", "fees": "शुल्क", "time": "समय", "timing": "समय",
    "hours": "समय", "patient": "मरीज़",
    "morning": "सुबह", "evening": "शाम", "today": "आज", "tomorrow": "कल",
    "sharma": "शर्मा", "mehta": "मेहता", "patel": "पटेल", "shah": "शाह",
    "parking": "पार्किंग", "insurance": "बीमा", "payment": "भुगतान",
    "document": "दस्तावेज़", "documents": "दस्तावेज़", "address": "पता",
    "location": "स्थान", "holiday": "छुट्टी", "cancel": "रद्द",
    "reschedule": "बदल", "human": "मानव", "emergency": "आपदा",
    "kabir": "कबीर", "meera": "मीरा", " Gujarati": "गुजરाती",
    "gujarati": "गुजराती", "hindi": "हिंदी", "english": "अंग्रेज़ी",
}
DEV_DIGITS = {ord(c): ord(str(i)) for i, c in enumerate("०१२३४५६७८९")}
GUJ_DIGITS = {ord(c): ord(str(i)) for i, c in enumerate("૦૧૨૩૪૫૬૭૮૯")}


def normalize_query(text: str, hinglish: bool = True) -> str:
    t = unicodedata.normalize("NFC", text).lower()
    t = t.translate(DEV_DIGITS).translate(GUJ_DIGITS)
    t = re.sub(r"[.,!?।]", " ", t)
    tokens = t.split()
    if hinglish:
        tokens = [HINGLISH_MAP.get(tok, tok) for tok in tokens]
    return " ".join(tokens)


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    section: str
    language: str
    content: str
    bm25_score: float
    dense_score: float
    rrf_score: float
    rank: int


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    confidence: float
    grounded: bool
    normalized_query: str
    backend: str
    execution_time_ms: float = 0.0


class HybridRetriever:
    def __init__(self, model_name: str | None = None, prefer_real: bool = True) -> None:
        self.embedder = DenseEmbedder(model_name or settings.embedding_model, prefer_real=prefer_real)
        self.chunks: list[Chunk] = []
        self.bm25: BM25Index | None = None
        self.vectors: np.ndarray | None = None
        self.corpus_blob: str = ""

    def build(self, chunks: list[Chunk]) -> None:
        self.chunks = list(chunks)
        if not self.chunks:
            self.bm25 = None
            self.vectors = None
            return
        self.bm25 = BM25Index([c.id for c in self.chunks], [c.content for c in self.chunks])
        self.vectors = self.embedder.embed([c.content for c in self.chunks])
        self.corpus_blob = " ".join(c.content for c in self.chunks).lower()

    def build_from_db(self, db: Session) -> None:
        self.build(list(db.scalars(__import__("sqlalchemy").select(Chunk)).all()))

    def query(self, text: str, top_k: int | None = None,
              min_confidence: float | None = None, hinglish: bool = True) -> RetrievalResult:
        import time
        start = time.perf_counter()
        top_k = top_k or settings.retrieval_top_k
        min_confidence = settings.retrieval_min_confidence if min_confidence is None else min_confidence
        norm = normalize_query(text, hinglish=hinglish)
        if not self.chunks or self.bm25 is None or self.vectors is None:
            return RetrievalResult([], 0.0, False, norm, self.embedder.backend)

        bm25_hits = dict(self.bm25.search(norm, top_n=max(top_k * 5, 20)))
        qvec = self.embedder.embed_query(norm)
        dense_scores = self.vectors @ qvec
        dense_order = np.argsort(-dense_scores)[: max(top_k * 5, 20)]
        dense_hits = {self.chunks[i].id: float(dense_scores[i]) for i in dense_order}

        rrf: dict[str, float] = {}
        for cid in set(bm25_hits) | set(dense_hits):
            score = 0.0
            if cid in bm25_hits:
                rank_b = sorted(bm25_hits, key=bm25_hits.get, reverse=True).index(cid) + 1
                score += 1.0 / (RRF_K + rank_b)
            if cid in dense_hits:
                rank_d = sorted(dense_hits, key=dense_hits.get, reverse=True).index(cid) + 1
                score += 1.0 / (RRF_K + rank_d)
            rrf[cid] = score

        ordered = sorted(rrf, key=rrf.get, reverse=True)[:top_k]
        by_id = {c.id: c for c in self.chunks}
        results: list[RetrievedChunk] = []
        for rank, cid in enumerate(ordered, 1):
            c = by_id[cid]
            results.append(RetrievedChunk(
                chunk_id=c.id, document_id=c.document_id, section=c.section,
                language=c.language, content=c.content,
                bm25_score=bm25_hits.get(cid, 0.0), dense_score=dense_hits.get(cid, 0.0),
                rrf_score=rrf[cid], rank=rank,
            ))
        # Confidence = does the corpus actually contain the query's distinctive
        # content? Pure rank-based RRF confidence is meaningless here because a
        # top-4 result always exists. A content-overlap gate lets unanswerable
        # questions be rejected instead of silently grounded (§7.4).
        content_tokens = [t.rstrip("'s") for t in norm.split()
                          if t not in STOP_TOKENS and len(t) > 1]
        if content_tokens:
            def covered(token: str) -> bool:
                if token in self.corpus_blob:
                    return True
                for group in SYNONYM_GROUPS:
                    if token in group and any(m in self.corpus_blob for m in group if m != token):
                        return True
                return False

            present = [t for t in content_tokens if covered(t)]
            coverage = len(present) / len(content_tokens)
            all_present = len(present) == len(content_tokens)
        else:
            coverage = 1.0 if ordered else 0.0
            all_present = bool(ordered)
        confidence = round(0.60 * float(all_present) + 0.40 * coverage, 4)
        return RetrievalResult(
            chunks=results, confidence=confidence, grounded=confidence >= min_confidence,
            normalized_query=norm, backend=self.embedder.backend,
            execution_time_ms=round((time.perf_counter() - start) * 1000, 2),
        )
