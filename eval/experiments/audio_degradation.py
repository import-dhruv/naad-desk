"""Telephone-band and noise degradation experiment (§11.4).

Generates fresh TTS audio, applies deterministic 8 kHz resampling and seeded
noise at 10 dB / 5 dB SNR, re-transcribes, and computes WER with paired
bootstrap confidence intervals. All measurements are real.
"""
from __future__ import annotations

import asyncio
import io
import json
import sys
import uuid
import wave
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from app.db.database import SessionLocal  # noqa: E402
from app.db.models import EvalRun, EvalSample  # noqa: E402
from app.gateway.oogam_client import oogam  # noqa: E402

from eval.metrics.bootstrap import paired_bootstrap  # noqa: E402
from eval.metrics.wer import wer  # noqa: E402

TTS_CODE = {"hi": "HIN", "gu": "GUJ", "en-in": "IEN"}
STT_CODE = {"hi": "HIN", "gu": "GUJ", "en-in": "ENG"}
VOICE = {"hi": "aditi", "gu": "kabir", "en-in": "aditi"}
PER_LANGUAGE = 4
SEED = 20261119


def wav_bytes(pcm: np.ndarray, rate: int) -> bytes:
    pcm = np.clip(pcm, -32768, 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


def read_wav(data: bytes) -> tuple[np.ndarray, int]:
    with wave.open(io.BytesIO(data), "rb") as w:
        rate = w.getframerate()
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype="<i2").astype(np.float64), rate


def degrade(pcm: np.ndarray, rate: int, condition: str) -> tuple[np.ndarray, int]:
    rng = np.random.default_rng(SEED)
    if condition == "8khz":
        return resample_poly(pcm, 1, 3).astype(np.float64), 8000
    if condition in ("snr10", "snr5"):
        target = 10 if condition == "snr10" else 5
        signal_power = np.mean(pcm ** 2) or 1.0
        noise_power = signal_power / (10 ** (target / 10))
        noise = rng.normal(0, np.sqrt(noise_power), len(pcm))
        return pcm + noise, rate
    return pcm, rate


async def transcribe(audio: bytes, lang: str) -> str:
    result = await oogam.stt(audio, STT_CODE[lang], verbose=False)
    return result.get("text", "")


async def main() -> None:
    rows = [json.loads(line) for line in (ROOT / "eval/datasets/utterances.jsonl").read_text(encoding="utf-8").splitlines()]
    selected = []
    for lang in TTS_CODE:
        selected += [r for r in rows if r["language"] == lang][:PER_LANGUAGE]

    run_id = f"eval-degrade-{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    db.add(EvalRun(id=run_id, kind="degradation", config_json=json.dumps({
        "conditions": ["clean", "8khz", "snr10", "snr5"], "per_language": PER_LANGUAGE,
        "seed": SEED, "resampling": "scipy.signal.resample_poly",
    }), git_sha="unknown"))
    db.commit()

    results: list[dict] = []
    for row in selected:
        lang = row["language"]
        try:
            audio = await oogam.tts(row["reference"], VOICE[lang], TTS_CODE[lang])
            pcm, rate = read_wav(audio)
            clean_h = await transcribe(audio, lang)
            clean_wer = wer(row["reference"], clean_h)
            for condition in ("8khz", "snr10", "snr5"):
                degraded, new_rate = degrade(pcm, rate, condition)
                hyp = await transcribe(wav_bytes(degraded, new_rate), lang)
                score = wer(row["reference"], hyp)
                results.append({"sample_id": row["sample_id"], "language": lang,
                                "condition": condition, "clean_wer": clean_wer, "wer": score,
                                "degradation": round(score - clean_wer, 4)})
                db.add(EvalSample(run_id=run_id, sample_id=row["sample_id"], condition=condition,
                                  reference=row["reference"], hypothesis=hyp, metric="wer", value=score))
            db.commit()
        except Exception as exc:
            print(f"  {row['sample_id']}: error {exc}")
    db.close()

    by_condition: dict[str, list[float]] = {}
    paired: dict[str, dict] = {}
    for condition in ("8khz", "snr10", "snr5"):
        subset = [r for r in results if r["condition"] == condition]
        by_condition[condition] = round(sum(r["wer"] for r in subset) / len(subset), 4) if subset else None
        paired[condition] = paired_bootstrap(
            [r["wer"] for r in subset], [r["clean_wer"] for r in subset], seed=SEED) if subset else None

    metrics = {"condition_wer": by_condition, "paired_bootstrap_vs_clean": paired,
               "completed_trials": len(results), "failed_trials": len(selected) * 3 - len(results)}
    db = SessionLocal()
    run = db.get(EvalRun, run_id)
    run.metrics_json = json.dumps(metrics)
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.close()

    out = ROOT / "eval/reports/degradation_results.json"
    out.write_text(json.dumps({"run_id": run_id, "metrics": metrics, "samples": results},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print("Degradation metrics:", json.dumps(metrics, indent=2))
    await oogam.close()


if __name__ == "__main__":
    asyncio.run(main())
