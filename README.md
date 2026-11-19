# Naad Desk

A production-style, end-to-end Indian-language voice AI engineering showcase built on
**Oogam Naad Realtime (naad-sts-v2)** and **Sutra (sutra-conversation)**. It includes a
browser voice agent, deterministic appointment tooling, hybrid multilingual retrieval,
post-call analytics, an independent evaluation lab, and a professional engineering dashboard.

All clinic data is **synthetic**. The API key stays on the server.

---

## Quick start (fresh clone, <15 min)

```bash
# 1. Python 3.12 + Node 20 required
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Configure credentials (never commit this file)
cp .env.example .env
#    edit OOGAM_API_KEY in .env

# 3. Build the frontend
cd frontend && npm install && npm run build && cd ..

# 4. Run the backend (serves API + built dashboard)
cd backend && ../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8100
```

Open `http://localhost:8100`. The backend auto-seeds 4 doctors, 3 weeks of slots,
30 existing appointments, 17 genuine findings, and indexes the 65k-character
multilingual knowledge base on startup.

> Port 8100 is used because 8000 is often occupied locally. The Vite dev proxy and
> the scenario runner point at 8100. Change `APP_PORT`/proxy if needed.

**Docker:** `cp .env.example .env && docker compose up --build` → `http://localhost:8100`.

---

## What works

| Capability | Status |
|---|---|
| Browser mic → AudioWorklet → 16 kHz PCM16 streaming | implemented |
| 24 kHz gapless playback scheduler + instant flush | implemented |
| Realtime `session.updated → set_lang → set_voice → voice_ack → set_mode → mode_ack → session.update → say` | verified live |
| Barge-in (`stop_utterance → interrupted`) | verified live |
| Sutra `json_object` structured plans | verified live |
| Hybrid BM25 + dense RRF retrieval, multilingual KB (27 docs, 65,748 chars) | implemented |
| Grounded answers + unanswerable rejection | 96.7% grounded · 100% rejection (40-Q set) |
| Deterministic booking/reschedule/cancel with backend-enforced confirmation | implemented + tests |
| Concurrent booking safety (partial UNIQUE index + BEGIN IMMEDIATE) | tested |
| Medical / emergency / injection guardrails | tested |
| Dual-channel recording + batch STT + QA scoring + summaries | implemented |
| 24-scenario replay runner | 22/24 with evidence (see `recon/results/scenarios.md`) |
| WER, 8 kHz/SNR degradation, latency with bootstrap CIs | real measurements |
| 17 evidence-backed findings | implemented |
| 88 passing unit/integration tests | passing |

Measured (real): turn latency p50 **1,670 ms**, p95 **2,138 ms** (75 turns);
WER pooled **0.500** (32 TTS→STT trials, 4 languages); 8 kHz WER **0.406**,
5 dB SNR WER **0.442** (36 trials). See `eval/reports/EVALUATION_REPORT.md`.

---

## Repository map

```
backend/app/          gateway · orchestrator · retrieval · tools · analytics · api · db
frontend/src/         pages · components · audio · websocket · services · charts
knowledge/{en,hi,gu}/ 27 synthetic Markdown documents
eval/                 dataset (240 utterances) · experiments · metrics · reports
recon/                phase-0 probe · findings · 24-scenario results
docs/                 architecture, api, runbook, evaluation, findings, decisions, phase-0
scripts/              smoke test · KB generators · e2e socket test · scenario runner
```

Full requirement traceability: `docs/traceability.md`.
Engineering decisions: `docs/decisions.md`.
Phase 0 evidence: `docs/phase-0-findings.md`.

---

## Verify

```bash
.venv/bin/python -m pytest -q          # 88 tests
.venv/bin/python scripts/smoke_test.py # seed + ingest + retrieval + eval
scripts/e2e_socket_test.py             # full gateway -> upstream -> audio round trip
scripts/run_scenarios.py               # 24 replay scenarios (live backend required)
eval/reports/generate_report.py        # regenerate evaluation report
```

---

## Known limitations (honest)

- Real browser microphone capture cannot be exercised headlessly; the AudioWorklet
  path is implemented but not live-tested in CI. Typed `text_input` replay is used
  for automated scenarios.
- `sentence-transformers` is optional and not installed; dense retrieval uses a
  clearly-labelled deterministic hashed character-n-gram fallback. Install
  `sentence-transformers` to activate `intfloat/multilingual-e5-small`.
- Batch STT marks `timestampsEstimated: true`; no true diarization is claimed.
- Evaluation audio is synthetic TTS; consenting-speaker recordings (3 speakers for
  Hindi/Gujarati) are a documented remaining gap.
- TTS streaming and language-switch matrices require browser trials; empty states
  are shown rather than fabricated numbers.
- No wallet-balance read endpoint was found; a local spend guard is used.
- The Vercel deployment uses ephemeral `/tmp` SQLite (data resets on cold start) and
  is protected by Vercel Authentication. See `docs/deployment.md`; local/Docker is persistent.
