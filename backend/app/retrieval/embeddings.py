"""Dense multilingual embeddings with a labelled deterministic fallback (D-06).

Primary backend: sentence-transformers `intfloat/multilingual-e5-small` when the
optional dependency and model are available. Fallback: a deterministic hashed
character-n-gram vector (L2-normalised). The fallback is NOT a learned semantic
embedding; it is labelled `deterministic_char_hash` in every API response so no
one mistakes it for the real model.
"""
from __future__ import annotations

import hashlib
import unicodedata
from typing import Any

import numpy as np

DIMS = 384
NGRAM = 3


class DenseEmbedder:
    def __init__(self, model_name: str = "intfloat/multilingual-e5-small", prefer_real: bool = True) -> None:
        self.model_name = model_name
        self.model: Any = None
        self.backend = "deterministic_char_hash"
        if prefer_real:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore
                self.model = SentenceTransformer(model_name)
                self.backend = f"sentence-transformers:{model_name}"
            except Exception:
                self.model = None

    @property
    def dimension(self) -> int:
        if self.model is not None:
            return int(self.model.get_sentence_embedding_dimension())
        return DIMS

    def embed(self, texts: list[str]) -> np.ndarray:
        if self.model is not None:
            vectors = self.model.encode(
                [f"query: {t}" for t in texts], normalize_embeddings=True,
                convert_to_numpy=True, show_progress_bar=False,
            )
            return np.asarray(vectors, dtype=np.float32)
        return np.vstack([self._fallback(t) for t in texts])

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    def _fallback(self, text: str) -> np.ndarray:
        t = unicodedata.normalize("NFC", text).lower()
        vec = np.zeros(DIMS, dtype=np.float32)
        tokens = t.split()
        grams: list[str] = []
        for tok in tokens:
            padded = f"^{tok}$"
            for i in range(max(len(padded) - NGRAM + 1, 1)):
                grams.append(padded[i:i + NGRAM])
        for g in grams:
            h = hashlib.blake2b(g.encode("utf-8"), digest_size=8).digest()
            idx = int.from_bytes(h, "big") % DIMS
            vec[idx] += 1.0
        norm = float(np.linalg.norm(vec))
        if norm:
            vec /= norm
        return vec
