# Findings

17 evidence-backed findings were recorded from Phase 0 reconnaissance and the
first live experiments. Source: `recon/results/phase0_ws_probe.json`, live REST
probes, and the WER/degradation runs.

| ID | Severity | Area | Title |
|---|---|---|---|
| F-01 | low | realtime | Realtime voices catalogue exposes only four short codes |
| F-02 | medium | realtime | X-Naad headers absent on realtime WS handshake |
| F-03 | low | realtime | event_id not observed on v2 realtime frames |
| F-04 | low | realtime | set_lang produces no acknowledgement |
| F-05 | low | realtime | session.update accepted without confirmation |
| F-06 | low | audio | Binary agent audio arrives in ~341 ms frames |
| F-07 | medium | stt | Batch STT timestamps are explicitly estimated |
| F-08 | low | stt | Batch STT normalises code-mixed English into Devanagari |
| F-09 | low | sutra | Emotion tag behaviour differs between chat and realtime |
| F-10 | medium | models | Live model ids are -v2 while PRD baseline is -v1 |
| F-11 | medium | languages | Indian English codes differ across endpoints |
| F-12 | low | voices | REST voice 'kabir' mapped to realtime 'm2' |
| F-13 | medium | billing | No documented wallet-balance read endpoint |
| F-14 | medium | auth | No session-token mint endpoint documented |
| F-15 | low | realtime | say enforces a 500-character ceiling |
| F-16 | low | realtime | mode_ack includes undocumented is_emotion_tags field |
| F-17 | low | realtime | stop_utterance yields duplicated state:idle |

Each finding has expected vs actual behaviour, reproduction steps, an evidence
path, a suggested fix, and a status. Browse them at `/findings` or export with
`GET /api/findings/export.md`.

Classification: **bug** requires a confirmed deviation from documented behaviour;
most entries above are **limitations** or **observations**, which are labelled as
such. No bugs were invented to reach a target.
