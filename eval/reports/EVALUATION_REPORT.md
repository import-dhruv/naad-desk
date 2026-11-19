# Naad Desk — Evaluation Report

Generated: 2026-11-19T05:40:43.820427+00:00

## Executive summary

This report aggregates only experiments that were actually executed. Confidence intervals are bootstrap percentile intervals; a CI crossing zero is reported as non-significant rather than hidden.

## Methodology

- WER: JiWER with symmetric normalisation (NFC, lowercase, nukta removal, Indic digits to ASCII, punctuation stripping).
- Degradation: SciPy resample_poly to 8 kHz; seeded Gaussian noise at 10 dB and 5 dB SNR.
- Confidence intervals: 10,000 utterance-level bootstrap resamples (seed 20261119).
- Latency: server-side turn timestamps including the 700 ms VAD floor.

## Dataset

240 synthetic utterances (60 each: Gujarati, Hindi, Hinglish, Indian English) covering numbers, dates, times, names, clinic sentences, fillers and hesitations. `eval/datasets/utterances.jsonl` holds references; `eval/manifests/audio_manifest.json` holds checksums. Consenting-speaker recordings remain a documented limitation.

## Experiment results

### wer — `eval-wer-05f9540a`

Started: 2026-11-19 05:34:52 · git: unknown

Config: `{"trials": 32, "per_language": 8, "tts_model": "naad-tts-v2", "stt_model": "naad-stt-v2", "normalization": "NFC, lowercase, nukta, Indic digits to ASCII"}`

```json
{
  "pooled_wer": 0.5003,
  "macro_wer": 0.5003,
  "by_language": {
    "hi": 0.4069,
    "gu": 0.4756,
    "hinglish": 0.9762,
    "en-in": 0.1424
  },
  "ci_pooled": {
    "mean": 0.5003,
    "ci_low": 0.3713,
    "ci_high": 0.6413,
    "resamples": 10000,
    "seed": 20261119
  },
  "completed_trials": 32,
  "failed_trials": 0,
  "conditions": [
    "clean"
  ],
  "sample_rate_hz": 16000
}
```

### degradation — `eval-degrade-ec756b65`

Started: 2026-11-19 05:38:03 · git: unknown

Config: `{"conditions": ["clean", "8khz", "snr10", "snr5"], "per_language": 4, "seed": 20261119, "resampling": "scipy.signal.resample_poly"}`

```json
{
  "condition_wer": {
    "8khz": 0.4059,
    "snr10": 0.3721,
    "snr5": 0.4415
  },
  "paired_bootstrap_vs_clean": {
    "8khz": {
      "difference": 0.0477,
      "ci_low": -0.0182,
      "ci_high": 0.1641,
      "significant": false,
      "resamples": 10000,
      "seed": 20261119
    },
    "snr10": {
      "difference": 0.0139,
      "ci_low": -0.0409,
      "ci_high": 0.0661,
      "significant": false,
      "resamples": 10000,
      "seed": 20261119
    },
    "snr5": {
      "difference": 0.0833,
      "ci_low": -0.0062,
      "ci_high": 0.2065,
      "significant": false,
      "resamples": 10000,
      "seed": 20261119
    }
  },
  "completed_trials": 36,
  "failed_trials": 0
}
```

### latency — `eval-latency-605aa093`

Started: 2026-11-19 05:40:43 · git: unknown

Config: `{"source": "turns.t_turn_complete", "vad_floor_ms": 700}`

```json
{
  "turn_count": 75,
  "p50_ms": 1670.27,
  "p95_ms": 2137.81,
  "mean_ms": 1541.4,
  "min_ms": 0.03,
  "max_ms": 2694.28,
  "worst_5_percent": [
    2148.82,
    2295.03,
    2694.28
  ],
  "p50_ci": {
    "mean": 1670.27,
    "ci_low": 1494.99,
    "ci_high": 1759.4,
    "resamples": 10000,
    "seed": 20261119
  },
  "vad_floor_ms": 700,
  "note": "Timing comes from server-side turn instrumentation; VAD 700 ms floor included."
}
```

## Limitations

- No real consenting-speaker audio; WER experiments use synthetic TTS audio.
- Batch STT timestamps are estimated; no diarization claims are made.
- TTS streaming and language-switch matrices require browser-side trials and are not fabricated here.
- Cost figures are estimates from published rates unless X-Naad-Cost-Paise is present.

## Reproduction

```bash
.venv/bin/python eval/datasets/build_dataset.py
.venv/bin/python eval/experiments/wer_experiment.py
.venv/bin/python eval/experiments/audio_degradation.py
.venv/bin/python eval/experiments/latency_experiment.py
.venv/bin/python eval/reports/generate_report.py
```

## Raw data references

- `eval/reports/wer_results.json`
- `eval/reports/degradation_results.json`
- `eval/reports/latency_results.json`
- `recon/results/phase0_ws_probe.json`
- `recon/results/scenarios.json`
