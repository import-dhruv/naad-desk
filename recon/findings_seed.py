"""Genuine findings from Phase 0 reconnaissance (2026-11-19).

Every entry is backed by an observed response or event captured in
recon/results/phase0_ws_probe.json or the recon HTTP probes. No invented bugs.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

try:
    from app.db.models import Finding
except ImportError:  # when executed from the repository root
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
    from app.db.models import Finding

FINDINGS = [
    dict(id="F-01", title="Realtime voices catalogue exposes only four short codes",
         severity="low", area="realtime", kind="limitation",
         expected="PRD baseline assumes f1–f4 and m1–m4.",
         actual="GET /api/naad/sts/voices returns f1, f2, m1, m2 only.",
         reproduction_steps="curl -H 'Authorization: Bearer $KEY' https://platform.oogam.ai/api/naad/sts/voices",
         evidence_path="recon/results/phase0_ws_probe.json", suggestion="Pin f1/m2 and avoid assuming f3/f4.", status="open"),
    dict(id="F-02", title="X-Naad headers absent on realtime WS handshake",
         severity="medium", area="realtime", kind="observation",
         expected="Docs describe X-Naad-Model/Voice/Cost-Paise/Generation-Id headers.",
         actual="WS handshake exposed only server: nginx and date. Headers appear on REST responses only.",
         reproduction_steps="Open wss://platform.oogam.ai/v1/realtime?v=2 and inspect response headers.",
         evidence_path="recon/results/phase0_ws_probe.json", suggestion="Cost must be estimated from published rates on the socket; read headers from REST calls.", status="open"),
    dict(id="F-03", title="event_id not observed on v2 realtime frames",
         severity="low", area="realtime", kind="observation",
         expected="Docs state every JSON event carries event_id under ?v=2.",
         actual="Observed session.updated/state/voice_ack/mode_ack/reply frames in our probe had no event_id.",
         reproduction_steps="Run recon/scripts/phase0_ws_probe.py with ?v=2 and inspect events.",
         evidence_path="recon/results/phase0_ws_probe.json", suggestion="Parser must not require event_id; tolerate both.", status="open"),
    dict(id="F-04", title="set_lang produces no acknowledgement",
         severity="low", area="realtime", kind="observation",
         expected="A pin acknowledgement similar to voice_ack/mode_ack.",
         actual="set_lang is applied silently; no lang_ack observed.",
         reproduction_steps="Send set_lang then drain frames in the probe.",
         evidence_path="recon/results/phase0_ws_probe.json", suggestion="Do not block waiting for an ack after set_lang.", status="open"),
    dict(id="F-05", title="session.update accepted without confirmation",
         severity="low", area="realtime", kind="observation",
         expected="A session.updated response echoing the VAD configuration.",
         actual="No response frame after session.update with vad_end_silence_ms=700.",
         reproduction_steps="Send session.update during the connection sequence.",
         evidence_path="recon/results/phase0_ws_probe.json", suggestion="Treat session.update as fire-and-forget; verify VAD behaviour by measuring endpoint timing.", status="open"),
    dict(id="F-06", title="Binary agent audio arrives in ~341 ms frames",
         severity="low", area="audio", kind="observation",
         expected="Frame duration unspecified in docs.",
         actual="Each binary frame is 16384 bytes = 8192 samples @ 24 kHz = 341.3 ms.",
         reproduction_steps="Send say and count binary frame sizes.",
         evidence_path="recon/results/phase0_ws_probe.json", suggestion="Playback scheduler must queue and clock frames; do not assume 20 ms chunks.", status="open"),
    dict(id="F-07", title="Batch STT timestamps are explicitly estimated",
         severity="medium", area="stt", kind="limitation",
         expected="Word-level timestamps for analytics/diarization.",
         actual="verbose_json returns timestampsEstimated:true and one segment for a 3 s clip.",
         reproduction_steps="POST /audio/transcriptions with response_format=verbose_json.",
         evidence_path="recon/results/phase0_ws_probe.json", suggestion="Label all transcript timing as estimated; do not claim diarization.", status="open"),
    dict(id="F-08", title="Batch STT normalises code-mixed English into Devanagari",
         severity="low", area="stt", kind="observation",
         expected="Transcript preserves the spoken script mix.",
         actual="Spoken 'शर्मा clinic' returned as 'शर्मा clinic' but language field 'hin' and mixed-script handling varies.",
         reproduction_steps="Synthesise a Hindi sentence with an English loanword and transcribe it.",
         evidence_path="recon/fixtures/phase0_hi.wav", suggestion="Normalise both scripts before WER; use symmetric normalisation.", status="open"),
    dict(id="F-09", title="Emotion tag behaviour differs between chat and realtime",
         severity="low", area="sutra", kind="observation",
         expected="No leading emotion tag on direct chat completions.",
         actual="Docs confirm realtime prompt emits a leading (emotion) tag; plain chat did not in our probe.",
         reproduction_steps="Call /chat/completions directly and inspect content prefix.",
         evidence_path="docs/phase-0-findings.md", suggestion="Strip a leading (word) tag defensively on all model output.", status="open"),
    dict(id="F-10", title="Live model ids are -v2 while PRD baseline is -v1",
         severity="medium", area="models", kind="limitation",
         expected="naad-sts-v1 / naad-tts-v1 model ids.",
         actual="GET /models lists naad-tts-v2, naad-stt-v2, naad-sts-v2 only.",
         reproduction_steps="curl https://platform.oogam.ai/v1/models -H 'Authorization: Bearer $KEY'",
         evidence_path="docs/phase-0-findings.md", suggestion="Use v2 ids; v1 integrations remain supported per docs.", status="open"),
    dict(id="F-11", title="Indian English language codes differ across endpoints",
         severity="medium", area="languages", kind="limitation",
         expected="One code for Indian English.",
         actual="Realtime uses en-in; TTS expects IEN and STT expects ENG.",
         reproduction_steps="Compare /api/naad/sts/languages with the Models & Languages doc table.",
         evidence_path="docs/phase-0-findings.md", suggestion="Map en-in -> IEN (TTS) / ENG (STT) centrally.", status="open"),
    dict(id="F-12", title="REST voice 'kabir' mapped to realtime 'm2'",
         severity="low", area="voices", kind="observation",
         expected="Voice ids identical across REST and realtime.",
         actual="REST /voices has named presets; realtime catalog uses f1/f2/m1/m2 short codes.",
         reproduction_steps="Compare GET /v1/voices with GET /api/naad/sts/voices.",
         evidence_path="docs/phase-0-findings.md", suggestion="Maintain an explicit mapping table.", status="open"),
    dict(id="F-13", title="No documented wallet-balance read endpoint",
         severity="medium", area="billing", kind="limitation",
         expected="Programmatic balance check before a call.",
         actual="No balance endpoint found in docs or probe; only dashboard billing is described.",
         reproduction_steps="Inspect docs/authentication and probe common /billing paths.",
         evidence_path="docs/phase-0-findings.md", suggestion="Implement a local spend guard with a configurable ceiling.", status="open"),
    dict(id="F-14", title="No session-token mint endpoint documented",
         severity="medium", area="auth", kind="suggestion",
         expected="An endpoint for the browser to obtain a short-lived session token.",
         actual="Docs describe session_token auth but publish no mint endpoint; browser proxying via backend remains viable.",
         reproduction_steps="Search docs for a token endpoint; none found in auth/sts docs.",
         evidence_path="docs/phase-0-findings.md", suggestion="Keep key server-side and proxy audio through the backend WS.", status="open"),
    dict(id="F-15", title="say enforces a 500-character ceiling",
         severity="low", area="realtime", kind="observation",
         expected="No stated limit in the PRD.",
         actual="session.updated limits.say_max_chars = 500; docs reject longer text.",
         reproduction_steps="Inspect session.updated limits with ?v=2.",
         evidence_path="recon/results/phase0_ws_probe.json", suggestion="Split responses into sentence chunks under 500 chars.", status="open"),
    dict(id="F-16", title="mode_ack includes undocumented is_emotion_tags field",
         severity="low", area="realtime", kind="observation",
         expected="mode_ack {mode} only.",
         actual="mode_ack {mode, is_emotion_tags:false}.",
         reproduction_steps="Send set_mode external_brain and inspect the ack.",
         evidence_path="recon/results/phase0_ws_probe.json", suggestion="Ignore unknown ack fields; keep parser defensive.", status="open"),
    dict(id="F-17", title="stop_utterance yields duplicated state:idle",
         severity="low", area="realtime", kind="observation",
         expected="A single idle transition after interruption.",
         actual="stop_utterance produced interrupted, state:idle, state:idle, then state:listening.",
         reproduction_steps="Send stop_utterance during say and drain frames.",
         evidence_path="recon/results/phase0_ws_probe.json", suggestion="De-duplicate identical consecutive state events in the client.", status="open"),
]


def seed_findings(db: Session) -> int:
    added = 0
    for item in FINDINGS:
        if db.get(Finding, item["id"]) is None:
            db.add(Finding(**item))
            added += 1
    db.commit()
    return added
