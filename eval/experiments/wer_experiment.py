"""Reproducible WER experiment with real TTS->STT round trips.

Only executed trials are recorded. No WER value is fabricated; if an upstream
call fails, that sample is marked as failed and excluded from the aggregate.
"""
from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import settings  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.db.models import EvalRun, EvalSample  # noqa: E402
from app.gateway.oogam_client import oogam  # noqa: E402

sys.path.insert(0, str(ROOT))
from eval.metrics.bootstrap import bootstrap_metric  # noqa: E402
from eval.metrics.wer import normalize, wer  # noqa: E402

TTS_CODE = {"hi": "HIN", "gu": "GUJ", "hinglish": "HIN", "en-in": "IEN"}
STT_CODE = {"hi": "HIN", "gu": "GUJ", "hinglish": "HIN", "en-in": "ENG"}
VOICE = {"hi": "aditi", "gu": "kabir", "hinglish": "aditi", "en-in": "aditi"}
PER_LANGUAGE = 8


def _git_sha() -> str:
    import subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


async def main() -> None:
    rows = [json.loads(line) for line in (ROOT / "eval/datasets/utterances.jsonl").read_text(encoding="utf-8").splitlines()]
    selected = []
    for lang in TTS_CODE:
        selected += [r for r in rows if r["language"] == lang][:PER_LANGUAGE]

    run_id = f"eval-wer-{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    db.add(EvalRun(id=run_id, kind="wer", config_json=json.dumps({
        "trials": len(selected), "per_language": PER_LANGUAGE,
        "tts_model": settings.tts_model, "stt_model": settings.stt_model,
        "normalization": "NFC, lowercase, nukta, Indic digits to ASCII",
    }), git_sha=_git_sha()))
    db.commit()

    samples = []
    for row in selected:
        lang = row["language"]
        try:
            audio = await oogam.tts(row["reference"], VOICE[lang], TTS_CODE[lang])
            result = await oogam.stt(audio, STT_CODE[lang], verbose=False)
            hypothesis = result.get("text", "")
            score = wer(row["reference"], hypothesis)
            status = "ok"
        except Exception as exc:
            hypothesis = ""
            score = None
            status = f"error: {type(exc).__name__}"
        samples.append({
            "sample_id": row["sample_id"], "condition": "clean", "language": lang,
            "reference": row["reference"], "hypothesis": hypothesis,
            "wer": score, "normalized_reference": normalize(row["reference"]),
            "normalized_hypothesis": normalize(hypothesis), "status": status,
        })
        db.add(EvalSample(run_id=run_id, sample_id=row["sample_id"], condition="clean",
                          reference=row["reference"], hypothesis=hypothesis, metric="wer",
                          value=score if score is not None else -1))
        db.commit()
        print(f"  {row['sample_id']}: {status} WER={score}")

    valid = [s for s in samples if s["wer"] is not None]
    by_lang: dict[str, list[float]] = {}
    for s in valid:
        by_lang.setdefault(s["language"], []).append(s["wer"])
    metrics = {
        "pooled_wer": round(sum(s["wer"] for s in valid) / len(valid), 4) if valid else None,
        "macro_wer": round(sum(sum(v) / len(v) for v in by_lang.values()) / len(by_lang), 4) if by_lang else None,
        "by_language": {k: round(sum(v) / len(v), 4) for k, v in by_lang.items()},
        "ci_pooled": bootstrap_metric([s["wer"] for s in valid], resamples=10000) if valid else None,
        "completed_trials": len(valid), "failed_trials": len(samples) - len(valid),
        "conditions": ["clean"], "sample_rate_hz": 16000,
    }
    run = db.get(EvalRun, run_id)
    run.metrics_json = json.dumps(metrics)
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.close()

    out = ROOT / "eval/reports/wer_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"run_id": run_id, "metrics": metrics, "samples": samples},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print("WER metrics:", json.dumps(metrics, indent=2))
    await oogam.close()


if __name__ == "__main__":
    asyncio.run(main())
