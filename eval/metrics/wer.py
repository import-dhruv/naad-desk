"""Word Error Rate with symmetric multilingual normalisation (§11.2)."""
from __future__ import annotations

import re
import unicodedata

import jiwer

DEV_DIGITS = {ord(c): ord(str(i)) for i, c in enumerate("०१२३४५६७८९")}
GUJ_DIGITS = {ord(c): ord(str(i)) for i, c in enumerate("૦૧૨૩૪૫૬૭૮૯")}

# Nukta removal (Devanagari nukta U+093C, Gujarati nukta U+0A3C)
NUKTA = {0x093C: None, 0x0A3C: None}


def normalize(text: str) -> str:
    """NFC, lowercase Latin, remove punctuation, nukta, Indic digits -> ASCII."""
    text = unicodedata.normalize("NFC", text)
    text = text.translate(DEV_DIGITS).translate(GUJ_DIGITS).translate(NUKTA)
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def wer(reference: str, hypothesis: str) -> float:
    ref, hyp = normalize(reference), normalize(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    return float(jiwer.wer(ref, hyp))


def corpus_wer(pairs: list[tuple[str, str]]) -> float:
    """Pooled WER: total edits / total reference words."""
    refs = [normalize(r) for r, _ in pairs]
    hyps = [normalize(h) for _, h in pairs]
    if not refs:
        return 0.0
    return float(jiwer.wer(refs, hyps))


def macro_wer(by_language: dict[str, list[tuple[str, str]]]) -> float:
    if not by_language:
        return 0.0
    values = [corpus_wer(pairs) for pairs in by_language.values()]
    return round(sum(values) / len(values), 4)
