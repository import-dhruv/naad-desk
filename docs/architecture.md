# Architecture

```
Browser (React + Vite + TS + Tailwind)
  AudioWorklet capture (16 kHz PCM16, true resampling, 20 ms)
  PlaybackScheduler (24 kHz, gapless, instant flush)
  CallSocket (versioned JSON protocol)
        │ WS /ws/call
FastAPI gateway
  gateway/websocket.py     versioned message validation
  gateway/session.py       per-call state, recording, latency, barge-in
  gateway/realtime_client  upstream socket, defensive parser, reconnect
  gateway/oogam_client     Sutra / TTS / STT REST + cost + spend guard
        │ WSS wss://platform.oogam.ai/v1/realtime?v=2
Oogam Naad STS (VAD, STT, TTS)      Oogam Sutra (structured plans)
        │
Conversation orchestrator
  state · prompts · engine · response_composer · guardrails · language
  one structured plan per turn, 1 retry, exact DB figures injected after generation
        │
Retrieval engine          chunking → BM25 + dense → RRF → confidence gate
Business tools            availability · booking · reschedule · cancel · fees · handoff
Analytics                 dual-channel STT → merge → extraction → QA → summary
Evaluation lab            WER · degradation · latency · bootstrap · report
SQLite (SQLAlchemy)       doctors · slots · appointments · calls · turns · tool_calls ·
                          retrievals · api_calls · analytics · eval_* · findings
```

## Design rules
- External brain mode: the engine owns reasoning and transactions; the speech
  engine owns VAD/STT/TTS.
- No LLM-authored figures. Fees, times, dates, IDs come from SQLite and are
  spoken via deterministic templates.
- Confirmation is a backend state machine (`tools/confirmation.py`), not a prompt.
- Retrieval confidence gates answering; low confidence → "unavailable" + handoff.
- All caller input and retrieved chunks are treated as untrusted data.
- The API key never leaves the backend.
