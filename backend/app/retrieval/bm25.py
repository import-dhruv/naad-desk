"""Keyword retrieval with BM25 (§7.2A)."""
from __future__ import annotations

import re
import unicodedata

from rank_bm25 import BM25Okapi

DEV_DIGITS = {ord(c): ord(str(i)) for i, c in enumerate("०१२३४५६७८९")}
GUJ_DIGITS = {ord(c): ord(str(i)) for i, c in enumerate("૦૧૨૩૪૫૬૭૮૯")}


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text).lower()
    text = text.translate(DEV_DIGITS).translate(GUJ_DIGITS)
    tokens = re.findall(r"[\w]+", text, flags=re.UNICODE)
    return [t for t in tokens if t]


class BM25Index:
    def __init__(self, chunk_ids: list[str], contents: list[str]) -> None:
        self.chunk_ids = list(chunk_ids)
        self.corpus = [tokenize(c) for c in contents]
        self.model = BM25Okapi(self.corpus) if self.corpus else None

    def search(self, query: str, top_n: int = 20) -> list[tuple[str, float]]:
        if self.model is None:
            return []
        scores = self.model.get_scores(tokenize(query))
        ranked = sorted(zip(self.chunk_ids, scores), key=lambda x: x[1], reverse=True)
        return [(cid, float(score)) for cid, score in ranked if score > 0][:top_n]
