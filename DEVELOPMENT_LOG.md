# Development Log

## 2026-11-19 — Phase 0 (reconnaissance)

**Completed**
- Inspected environment: Python 3.12.3 (`/usr/bin/python3.12`), Node 20.20.1, npm 10.8.2, Docker 29.0.2, ffmpeg 6.1.1, 145 GB free. Key not found in existing env.
- Verified credentials: `GET /models` 200 (naad + sutra products), `GET /voices` 200.
- Verified Sutra `json_object` structured output, TTS (24 kHz PCM16 WAV), batch STT verbose_json (`timestampsEstimated:true`).
- Verified realtime protocol live: `session.updated` capabilities, `set_lang`/`set_voice`→`voice_ack`/`set_mode external_brain`→`mode_ack`/`session.update`/`say`→`reply`→binary PCM audio, `stop_utterance`→`interrupted`.
- Created `docs/phase-0-findings.md`, `docs/traceability.md`, `docs/decisions.md`, `recon/results/phase0_ws_probe.json`, `recon/scripts/phase0_ws_probe.py`.
- Created project venv `.venv` and installed backend dependencies.

**Current task**
- Backend foundation: config, logging, SQLAlchemy models, seed data.

**Tests executed**
- Live API probes (curl + Python websockets): all 200 / expected events. No pytest suite yet.

**Tests passed / failed**
- Passed: auth, models, voices, Sutra JSON, TTS, STT, realtime flow, barge-in.
- Failed: initial WS probe used legacy `additional_headers`; fixed by switching to `websockets.asyncio.client.connect`.

**Known bugs**
- None blocking.

**Technical blockers**
- `sentence-transformers` not installed → dense retrieval uses labelled deterministic fallback until optional install.

**Next actions**
1. Build db models + seed.
2. Tools (date resolver, availability, booking, etc.) + unit tests.
3. Retrieval (chunking, BM25, embeddings, hybrid, ingestion) + KB docs.
4. Orchestrator + gateway + realtime session.
5. Analytics, eval lab, findings API.
6. Frontend dashboard.
7. Docker, CI, full test run, README.

---

## Milestone — Backend foundation + retrieval (Days 1–4)

**Completed**
- SQLAlchemy models for all 13 entities + holidays + KB docs/chunks; WAL, FKs,
  partial unique index on live appointments.
- Seed: 4 doctors, 816 slots, 30 appointments, 2 holidays.
- Multilingual KB: 27 documents / 65,748 characters (en/hi/gu), idempotent
  content-hash ingestion, heading-aware chunking.
- Hybrid retrieval: BM25 + dense (labelled deterministic fallback) + RRF,
  confidence gate. 40-question eval: Recall@4 0.767, groundedness 0.967,
  unanswerable rejection 1.000.
- Deterministic tools: availability, booking, reschedule, cancel, fees, handoff;
  backend-enforced confirmation tokens; Asia/Kolkata date resolution with
  transliteration aliases.

**Tests:** 88 pytest tests covering dates, tools, concurrency, retrieval,
guardrails, schemas, WER, bootstrap, QA scoring. 3 consecutive clean runs.

## Milestone — Orchestrator, gateway, analytics (Days 3–7)

**Completed**
- Sutra `json_object` structured plans with one retry; exact DB figures injected
  after generation; sentence-level `say` chunks <500 chars.
- Realtime client with verified handshake, defensive parser, bounded 1/2/4 s
  reconnect, 4402/1011 handling; barge-in via `stop_utterance` → `interrupted`.
- Dual-channel recording, batch STT, estimated-timestamp labelling, extracted
  JSON, QA rubric, three-bullet summaries.
- REST + WS API; FastAPI startup auto-seeds and indexes.
- Fixed: browser close frame racing `call.ended`; natural-language dates reaching
  tools unresolved; false handoff from LLM confirmation flag; Hindi/Gujarati doctor
  aliases.

**Live verification:** `scripts/e2e_socket_test.py` → session.ready, recording
notice, 3 captions, 38–48 binary audio frames, tool + retrieval + timing events,
`call.ended`. Fee question answered with exact DB value (500).

## Milestone — Evaluation lab, dashboard, packaging (Days 8–10)

**Completed**
- 24-scenario replay runner: latest run 12 pass / 10 observed-with-evidence /
  2 nondeterministic failures (22/24 with evidence). Results in
  `recon/results/scenarios.{json,md}`.
- Eval dataset 240 utterances; WER experiment 32 real TTS→STT trials (pooled
  0.5003, 95% CI [0.3713, 0.6413]); degradation 36 trials (8 kHz 0.4059,
  10 dB 0.3721, 5 dB 0.4415, paired CIs honestly non-significant); latency 75
  turns (p50 1,670 ms, p95 2,138 ms).
- Report generator → `eval/reports/EVALUATION_REPORT.md`.
- React dashboard: 8 routes, dark-first design, Recharts, real data only.
- 17 genuine findings seeded from reconnaissance.
- Dockerfile + compose + CI; Docker image built and container verified serving
  API 200 and dashboard 200.

**Known bugs:** none blocking. Remaining gaps are documented in README and
`docs/evaluation.md` (no consenting-speaker audio, no TTS-streaming / switch
matrix, browser mic not headlessly testable).

**Next actions:** none required for MVP; buffer items are the documented P1 gaps.
