# Requirement Traceability Matrix (MVP)

Status legend: `[x]` implemented in MVP, `[~]` partial / limited, `[ ]` deferred with reason.
This matrix tracks the PRD's P0 items against concrete modules. It is updated at milestones.

| PRD § | Requirement | Module / path | Status | Notes |
|---|---|---|---|---|
| 5.1 | Call UI (start/end, captions, states, timer, cost) | `frontend/src/pages/LiveCall.tsx` | [x] | dark-first, professional |
| 5.2 | AudioWorklet capture 16k mono PCM16 20ms + true resample + record | `frontend/src/audio/capture.ts`, `pcm-worklet.js` | [x] | AudioWorklet + linear resample |
| 5.3 | Gapless 24k playback scheduler + flush + interrupt + record | `frontend/src/audio/playback.ts` | [x] | clock-scheduled queue |
| 5.4 | Realtime integration + defensive parser | `gateway/realtime_client.py`, `gateway/session.py` | [x] | verified live; protocol in phase-0 doc |
| 5.5 | external_brain mode | `gateway/session.py` | [x] | mode_ack verified |
| 5.6 | Barge-in (stop, cancel, discard) | `gateway/session.py`, `frontend` | [x] | stop_utterance→interrupted verified |
| 6.1 | Per-turn orchestration, structured plan, retry | `orchestrator/engine.py` | [x] | Sutra json_object + 1 retry |
| 6.2 | Sutra integration (no native tools) | `gateway/oogam_client.py` | [x] | verified live |
| 6.3 | Sentence-level say <500 chars | `orchestrator/response_composer.py` | [x] | final:false/true streaming |
| 7.1–7.3 | KB >60k chars, 8–12 docs, hybrid RRF, Hinglish norm | `retrieval/*`, `knowledge/*` | [x] | 12 docs, 3 languages |
| 7.4 | Grounding + confidence threshold + 40-Q eval | `retrieval/hybrid.py`, `retrieval/evaluation.py` | [x] | 30 answerable/10 unanswerable |
| 8 | Tools: availability/book/reschedule/cancel/fees/handoff | `tools/*` | [x] | typed schemas |
| 8.1 | Confirmation enforced in backend | `tools/booking.py` | [x] | state machine, not prompt-only |
| 8.5 | Date resolution Asia/Kolkata, 4 languages | `tools/date_resolver.py` | [x] | ambiguity → clarify |
| 8.6 | Transaction safety, concurrent booking | `tools/booking.py`, `db/models.py` | [x] | UNIQUE(slot_id) + BEGIN IMMEDIATE |
| 9 | Guardrails: medical, emergency, injection, consent, masking | `orchestrator/guardrails.py` | [x] | 10+ injection tests |
| 10 | Analytics pipeline (dual channel, STT, extraction, QA, summary) | `analytics/*` | [x] | estimated timing labelled |
| 11 | Evaluation lab (WER, bootstrap, 8k/SNR, latency, TTS, switching) | `eval/*` | [~] | metrics + runners; live experiments require network/calls |
| 12 | Recon + findings log (15 genuine findings) | `recon/*`, `api/findings.py` | [~] | real findings from Phase 0 + recon script |
| 13 | SQLAlchemy models | `db/models.py` | [x] | all entities + indexes/FKs |
| 14 | REST + WS API | `api/*`, `gateway/websocket.py` | [x] | versioned WS protocol |
| 15–16 | Dashboard (premium dark UI, 7 nav sections) | `frontend/src/*` | [x] | real data only |
| 17 | Security, spend guard, reconnect | `config.py`, `gateway/realtime_client.py` | [x] | env-only key, masked phones |
| 18 | Structured JSON logging, latency waterfall | `logging.py`, `gateway/session.py` | [x] | per-call/turn ids |
| 19 | Unit/integration/e2e tests | `backend/tests/*` | [x] | 24-scenario runner |
| 20 | Repo structure | — | [x] | every module purposeful |
| 21–23 | Roadmap, metrics, demo | `docs/*`, `DEVELOPMENT_LOG.md` | [~] | report from real data; demo doc |

> `[~]` items depend on live network experiments or recorded audio that cannot be fully generated headlessly; the *frameworks* are implemented and report only executed results. No fabricated measurements.
