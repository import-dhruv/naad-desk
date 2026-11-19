# Phase 0 — Technical Reconnaissance & Findings

**Date:** 2026-11-19 (UTC)
**Scope:** Verify Oogam credentials, wallet/product access, realtime protocol, Sutra structured output, TTS/STT, and limits *before* large-scale development.
**Method:** Live calls against `https://platform.oogam.ai/v1/*` and `wss://platform.oogam.ai/v1/realtime` using the supplied key. Raw evidence in `recon/results/phase0_ws_probe.json`.

> The key is intentionally **not** recorded here or in any tracked file. It is supplied at runtime via `OOGAM_API_KEY`.

---

## 1. Verified facts (observed live on 2026-11-19)

### 1.1 Credentials & product access
| Check | Result | Evidence |
|---|---|---|
| Key format `sk-setu-…` | Valid | `GET /models` → 200 |
| Products enabled | `naad` + `sutra` | `/models` lists voice + chat models; `/chat/completions` → 200 |
| Sutra chat | Live | `sutra-conversation` present, `live: true` |
| Rate limit | default 60 req/min (per docs) | docs/auth; not stressed |

### 1.2 Model catalogue (`GET /models`)
```
sutra-conversation  chat   live:true
naad-tts-v2         tts    live:true
naad-stt-v2         stt    live:true
naad-sts-v2         sts    live:true
```
The PRD references `naad-sts-v1`; the live platform serves **`naad-sts-v2`** and `-v1` integrations remain supported. We use v2 ids and the `?v=2` realtime opt-in.

### 1.3 Realtime endpoint (`GET /api/naad/sts/v1/realtime/session`)
- WebSocket: `wss://platform.oogam.ai/v1/realtime` (legacy path `/ws`).
- **v2 opt-in:** `?v=2` on the URL — v1 default unchanged. Every JSON event carries `event_id` under v2 (not observed on our v1-style frames — see §2).
- Input audio: `pcm_s16le`, 16000 Hz, mono. Output: `pcm_s16le`, 24000 Hz, mono.
- `events_in`: `start_utterance`, `stop_utterance`, `reset`, `set_voice`, `set_lang`, `set_context`, `set_consent`, `set_mode`, `say` (+ v2: `ping`, `session.update`).
- `events_out`: `state`, `stt`, `reply`, `end`, `interrupted`, `context_ack`, `voice_ack`, `consent_ack`, `mode_ack`, `error` (+ v2: `conversation_initiation_metadata`, `pong`, `session.updated`).
- Format negotiation: `?in=…&out=…`; inputs `pcm_16000 / mulaw_8000 / alaw_8000`; outputs `pcm_24000 / pcm_16000 / pcm_8000 / mulaw_8000 / alaw_8000`.
- `say_max_chars = 500`; `kb_max_chars = 6000`; `context_system_max_chars = 8000`.
- Capabilities advertisement arrives as the **first** frame: `session.updated` with `{capabilities:{function_calling:true, parallel_tool_calls:false, max_tools:20, max_calls_per_turn:10, turn_grounding:false}, limits:{…}}`.

### 1.4 Observed call flow (exact frame order from probe)
1. Connect → first frame `session.updated` (capabilities + limits), then `state:idle`, `state:listening`.
2. `{"type":"set_lang","value":"hi"}` → **no explicit ack** (silent, applied).
3. `{"type":"set_voice","voice":"f1"}` → `voice_ack {voice_id, name, kind, gender, seed, locked}`.
4. `{"type":"set_mode","mode":"external_brain"}` → `mode_ack {mode, is_emotion_tags:false}`.
5. `{"type":"session.update","session":{vad_end_silence_ms:700, input_audio_format, output_audio_format}}` → accepted silently.
6. `{"type":"say","text":"…","final":false,"lang":"hi"}` then `final:true` → `state:thinking` → `reply {text, emotion, lang}` → `state:speaking` → **binary PCM frames** (16384 bytes each = 8192 samples @ 24 kHz ≈ 341 ms) → `end`.
7. `{"type":"stop_utterance"}` → `interrupted` → `state:idle` → `state:listening`.

**This satisfies the Phase 0 exit condition:** a backend-initiated spoken exchange produced real agent audio, and barge-in silenced it.

### 1.5 Voices
- REST `GET /voices` returns named presets (aditi/arjun/kabir available; ishaan/aria/dev disabled). No `live_voice_id` on presets.
- Realtime catalog `GET /api/naad/sts/voices`: **`f1` Aditi, `f2` Kavya, `m1` Arjun, `m2` Kabir** only (PRD assumed f1–f4/m1–m4 — discrepancy recorded as Finding F-01).
- Realtime languages `GET /api/naad/sts/languages`: 2-letter codes; `en-in` = Indian English, `en` = American English; `hi`, `gu`, etc. `auto` present but docs warn to pin a real code on turn 1.

### 1.6 Sutra structured output
`POST /chat/completions` with `response_format:{type:json_object}` → HTTP 200, valid JSON in `choices[0].message.content`, usage tokens reported. Model `sutra-conversation`. ✓

### 1.7 TTS / batch STT
- `POST /audio/speech` `{model:naad-tts-v2, input, voice, language:HIN}` → HTTP 200, WAV `PCM16 mono 24000 Hz`.
- `POST /audio/transcriptions` `{model:naad-stt-v2, language:HIN, response_format:verbose_json}` → `{text, language, duration, segments:[{start,end,text}], timestampsEstimated:true}`.
- **`timestampsEstimated: true`** confirms the PRD's warning: batch STT does NOT provide true word-level diarization. Our analytics labels all timings as estimated.

### 1.8 Handshake headers
Only `server: nginx` and `date` were exposed on the WS handshake. **No `X-Naad-*` headers on the realtime socket** — those are REST-only (to be probed per REST call in the recon module). Recorded as Finding F-02.

---

## 2. Unverified assumptions / open questions

- **Wallet balance**: no documented read endpoint; not queried. Spend is metered per connection-second/character. We implement a client-side spend guard with a configurable budget.
- **Event envelope under `?v=2`**: docs say every event carries `event_id`; probe used `?v=2` but observed no `event_id` on the frames shown (possibly only on v2-only events). Defensive parser must tolerate both. We therefore do **not** hard-require `event_id`.
- **`say` streaming cadence**: we confirmed `final:false`/`final:true` accumulates; exact flush semantics for long streams verified only with one greeting. Turn manager sends sentence chunks with `final:false` and a final `final:true`.
- **`set_consent`**: training opt-in defaults DENY; app sends `set_consent {training:false}` at call start for privacy.
- **Function calling (preview)**: capability advertised `true`, but we use `external_brain` + deterministic backend tools (PRD requirement), not engine tool calls.
- **Browser mic path**: cannot be exercised headlessly; browser client will use a server-minted session token (key never shipped to browser). This path is implemented but not live-tested in CI.

---

## 3. Blockers

None. Key is valid, all required products/models are live, realtime audio round-trip succeeded. Heavy optional dependency `sentence-transformers` is not installed; retrieval ships with a deterministic TF-IDF dense fallback (clearly labelled) and auto-upgrades to `intfloat/multilingual-e5-small` when available.

---

## 4. Budget & spend controls

- No wallet-read endpoint found. Design assumes a **prepaid wallet** and enforces `MAX_CALL_SECONDS`, `MONTHLY_BUDGET_PAISE`, and per-call `COST_CEILING_PAISE` locally (`.env`). Spend guard refuses new upstream requests when ceiling is hit.
- Approximate rates from docs: STS ₹0.38/min, TTS v2 ₹1.50/1k chars (turbo ₹0.75), Sutra ₹15/1M in · ₹60/1M out. Cost estimates in dashboard are **labelled estimates**; authoritative cost comes from `X-Naad-Cost-Paise` on REST responses where present.

---

## 5. Proposed technical decisions (see decisions.md)

1. Use v2 model ids and `?v=2` realtime opt-in; keep defensive parser for v1/v2 event shapes.
2. `external_brain` mode for deterministic control; backend owns LLM/retrieval/tools.
3. Browser auth via server-minted session token; key stays server-side.
4. Voice `f1` (Hindi) / `m2` (Gujarati-capable preset Kabir) pinned via `set_voice`; language via `set_lang` short codes.
5. Retrieval = BM25 + dense embeddings fused with RRF; dense backend auto-selects multilingual-e5-small when available, else deterministic labelled fallback.
6. All dates in Asia/Kolkata; all exact figures from SQLite; confirmation enforced in backend code.
7. Batch STT timings always labelled "estimated"; no diarization claims.

---

## 6. Phase 0 verification checklist (status)

- [x] Python / Node / disk / Docker inspected
- [x] Credentials valid, products enabled
- [x] Wallet/permissions status (wallet read N/A — documented)
- [x] Sutra availability + json_object verified
- [x] Realtime connection + first frames captured
- [x] `set_lang`/`set_voice`/`set_mode`/`session.update`/`say` sequence verified
- [x] Binary agent audio received
- [x] Barge-in (`stop_utterance` → `interrupted`) verified
- [x] TTS + batch STT + verbose_json verified
- [x] X-Naad header exposure checked
- [x] Findings documented (initial)

**Proceed to implementation.**
