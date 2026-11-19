"""One-command evaluation report generator from stored experiment results."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from app.db.database import SessionLocal  # noqa: E402
from app.db.models import EvalRun  # noqa: E402


def main() -> None:
    db = SessionLocal()
    runs = db.query(EvalRun).order_by(EvalRun.started_at).all()
    db.close()
    lines = [
        "# Naad Desk — Evaluation Report", "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}", "",
        "## Executive summary", "",
        "This report aggregates only experiments that were actually executed. "
        "Confidence intervals are bootstrap percentile intervals; a CI crossing zero "
        "is reported as non-significant rather than hidden.", "",
        "## Methodology", "",
        "- WER: JiWER with symmetric normalisation (NFC, lowercase, nukta removal, "
        "Indic digits to ASCII, punctuation stripping).",
        "- Degradation: SciPy resample_poly to 8 kHz; seeded Gaussian noise at 10 dB and 5 dB SNR.",
        "- Confidence intervals: 10,000 utterance-level bootstrap resamples (seed 20261119).",
        "- Latency: server-side turn timestamps including the 700 ms VAD floor.", "",
        "## Dataset", "",
        "240 synthetic utterances (60 each: Gujarati, Hindi, Hinglish, Indian English) "
        "covering numbers, dates, times, names, clinic sentences, fillers and hesitations. "
        "`eval/datasets/utterances.jsonl` holds references; `eval/manifests/audio_manifest.json` "
        "holds checksums. Consenting-speaker recordings remain a documented limitation.", "",
        "## Experiment results", "",
    ]
    for run in runs:
        metrics = json.loads(run.metrics_json or "{}")
        lines += [f"### {run.kind} — `{run.id}`", "",
                  f"Started: {run.started_at} · git: {run.git_sha}", "",
                  "Config: `" + (run.config_json or "{}") + "`", "",
                  "```json", json.dumps(metrics, indent=2, ensure_ascii=False), "```", ""]
    lines += [
        "## Limitations", "",
        "- No real consenting-speaker audio; WER experiments use synthetic TTS audio.",
        "- Batch STT timestamps are estimated; no diarization claims are made.",
        "- TTS streaming and language-switch matrices require browser-side trials and are not fabricated here.",
        "- Cost figures are estimates from published rates unless X-Naad-Cost-Paise is present.", "",
        "## Reproduction", "",
        "```bash",
        ".venv/bin/python eval/datasets/build_dataset.py",
        ".venv/bin/python eval/experiments/wer_experiment.py",
        ".venv/bin/python eval/experiments/audio_degradation.py",
        ".venv/bin/python eval/experiments/latency_experiment.py",
        ".venv/bin/python eval/reports/generate_report.py",
        "```", "",
        "## Raw data references", "",
        "- `eval/reports/wer_results.json`",
        "- `eval/reports/degradation_results.json`",
        "- `eval/reports/latency_results.json`",
        "- `recon/results/phase0_ws_probe.json`",
        "- `recon/results/scenarios.json`", "",
    ]
    out = ROOT / "eval/reports/EVALUATION_REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} ({len(runs)} runs)")


if __name__ == "__main__":
    main()
