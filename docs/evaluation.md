# Evaluation laboratory

## Dataset
240 synthetic utterances: 60 Gujarati, 60 Hindi, 60 Hinglish, 60 Indian English.
Fields: sample ID, language, category, speaker, reference transcript, audio path.
`eval/manifests/audio_manifest.json` stores SHA-256 checksums of reference text.
Consenting-speaker recordings are a documented gap.

## Metrics
- **WER** — JiWER with symmetric normalisation (NFC, lowercase Latin, punctuation
  removal, nukta removal, Devanagari/Gujarati digits → ASCII, whitespace collapse).
- **Pooled / macro / per-language WER** — from executed trials only.
- **Bootstrap CIs** — 10,000 utterance-level resamples, percentile 95%, seed 20261119.
- **Paired bootstrap** — for clean vs degraded comparisons; significance only when
  the CI excludes zero.

## Experiments actually run (2026-11-19)
| Experiment | Trials | Result |
|---|---|---|
| WER (TTS→STT, 4 languages) | 32 | pooled 0.5003; hi 0.4069, gu 0.4756, hinglish 0.9762, en-in 0.1424; 95% CI [0.3713, 0.6413] |
| 8 kHz degradation | 12 | WER 0.4059; paired diff +0.0477, CI [-0.0182, 0.1641] (not significant) |
| 10 dB SNR | 12 | WER 0.3721; paired diff +0.0139 (not significant) |
| 5 dB SNR | 12 | WER 0.4415; paired diff +0.0833, CI [-0.0062, 0.2065] (not significant) |
| Turn latency | 75 turns | p50 1,670 ms, p95 2,138 ms; p50 CI [1,495, 1,759] |
| Retrieval (40 questions) | 40 | Recall@4 0.767, groundedness 0.967, unanswerable rejection 1.000 |

The high Hinglish WER is a genuine observation: synthesising romanised text with the
Hindi TTS code produces pronunciation the STT model transcribes poorly. It is
reported, not smoothed over.

## Not run (no fabricated data)
- TTS streaming vs buffered TTFB (needs browser trials, 30 per mode per language).
- Language-switch matrix (6 pairs × 5 trials).
- 5/10-minute batch STT turnaround, concurrency 1/2/3/5.
- External KB vs built-in KB, default vs external_brain comparison.

Dashboard empty states mark these explicitly.

## Reproduce
```bash
.venv/bin/python eval/datasets/build_dataset.py
.venv/bin/python eval/experiments/wer_experiment.py
.venv/bin/python eval/experiments/audio_degradation.py
.venv/bin/python eval/experiments/latency_experiment.py
.venv/bin/python eval/reports/generate_report.py
```
