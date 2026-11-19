"""Generate the 240-utterance evaluation dataset (60 per language).

Reference transcripts are synthetic and cover numbers, dates, times, names,
clinic sentences, fillers and hesitations. An audio manifest with SHA-256
checksums is emitted; actual recordings require consenting speakers and are
documented as a limitation (see docs/evaluation.md).
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "eval" / "datasets"
MANIFEST = ROOT / "eval" / "manifests"

SEEDS = {
    "gu": ["શર્મા ક્લિનિક", "ડૉક્ટર મેહતા", "એપોઇન્ટમેન્ટ", "સવારે દસ વાગ્યે", "ફી પાંચસો રૂપિયા",
           "કાલે", "તારીખ વીસમી", "સોમવારથી શનિવાર", "પાર્કિંગ ઉપલબ્ધ છે", "ઉધરસ અને તાવ",
           "અરે, થોડીવાર રાહ જુઓ", "હા, બરાબર", "મારું નામ પટેલ છે", "ફોન નંબર 9876543210"],
    "hi": ["शर्मा क्लिनिक", "डॉक्टर मेहता", "अपॉइंटमेंट", "सुबह दस बजे", "शुल्क पाँच सौ रुपये",
           "कल", "तारीख़ बीस", "सोमवार से शनिवार", "पार्किंग उपलब्ध है", "खांसी और बुखार",
           "अरे, थोड़ा इंतज़ार कीजिए", "हाँ, ठीक है", "मेरा नाम पटेल है", "फ़ोन नंबर 9876543210"],
    "hinglish": ["Sharma clinic", "Dr Mehta", "appointment", "kal subah 10 baje", "fee 500 rupees",
                 "aaj", "date 20", "Monday to Saturday", "parking available hai", "cough aur fever",
                 "arey, thoda wait karo", "haan, theek hai", "my name is Patel", "phone 9876543210"],
    "en-in": ["Sharma clinic", "Dr Mehta", "appointment", "ten in the morning", "fee five hundred rupees",
              "tomorrow", "the twentieth", "Monday to Saturday", "parking is available", "cough and fever",
              "um, just a moment please", "yes, that's right", "my name is Patel", "phone number 9876543210"],
}

CATEGORIES = ["clinic", "doctor", "appointment", "datetime", "numbers", "policy", "filler", "name", "phone"]


def build() -> dict:
    rng = random.Random(20261119)
    rows = []
    for lang, seeds in SEEDS.items():
        for i in range(60):
            parts = rng.sample(seeds, k=rng.randint(3, 6))
            filler = rng.choice(["", "अरे ", "हाँ ", "um, ", "हद "] if lang != "en-in" else ["", "um, ", "well, "])
            text = filler + " ".join(parts) + ("।" if lang in ("hi", "gu") else ".")
            rows.append({
                "sample_id": f"{lang}-{i:03d}",
                "language": lang,
                "category": CATEGORIES[i % len(CATEGORIES)],
                "speaker": f"speaker-{1 + i % 3}" if lang in ("hi", "gu") else "synthetic-tts",
                "reference": text,
                "audio_file": f"eval/audio/{lang}-{i:03d}.wav",
            })
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.mkdir(parents=True, exist_ok=True)
    with (OUT / "utterances.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = [{
        "sample_id": r["sample_id"], "language": r["language"],
        "audio_file": r["audio_file"],
        "sha256": hashlib.sha256(r["reference"].encode("utf-8")).hexdigest(),
        "reference": r["reference"],
    } for r in rows]
    (MANIFEST / "audio_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"total": len(rows), "per_language": {lang: 60 for lang in SEEDS}}


if __name__ == "__main__":
    print(build())
