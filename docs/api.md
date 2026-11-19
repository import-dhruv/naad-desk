# API reference

## REST
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | app, DB and upstream configuration status |
| GET | `/api/config` | non-secret runtime flags for the frontend |
| POST | `/api/calls` | create a call session |
| GET | `/api/calls` | list call history |
| GET | `/api/calls/{id}` | full call detail (turns, tools, retrievals, analytics, API calls) |
| POST | `/api/calls/{id}/analyze` | trigger/re-run analytics |
| GET | `/api/calls/{id}/recording/{caller\|agent}` | dual-channel WAV |
| POST | `/api/kb/ingest` | idempotent document ingestion + index rebuild |
| GET | `/api/kb/documents` | indexed document metadata |
| GET | `/api/eval/runs` | stored experiment runs |
| POST | `/api/eval/run` | start an experiment (`{"kind":"retrieval"|"wer"|...}`) |
| GET | `/api/findings` | findings (filter by `severity`, `area`) |
| POST | `/api/findings` | create a finding |
| PATCH | `/api/findings/{id}` | update a finding |
| GET | `/api/findings/export.md` | Markdown export |

## WebSocket `/ws/call`
First frame must be:
```json
{"v":1,"type":"start","language":"hi","voice":null,"disclosure_ack":true}
```
Client → server: `audio` (base64 PCM16 16 kHz), `text_input` (scenario replay),
`interrupt`, `stop_playback`, `set_lang`, `end`, `ping`.

Server → client: `session.ready`, `recording.notice`, `caption`, `audio` (base64
PCM16 24 kHz), `state`, `timing`, `tool`, `retrieval`, `cost`, `stop_playback`,
`error`, `pong`, `call.ended`.

Every server frame has `type`, `call_id`, `ts` (monotonic) and `payload`.
Invalid frames produce an `error` frame; they never terminate the session.

Upstream event mapping is documented in `phase-0-findings.md`. The parser tolerates
both v1 and v2 envelopes and never requires `event_id`.
