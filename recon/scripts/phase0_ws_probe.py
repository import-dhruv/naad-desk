"""Phase 0 reconnaissance: capture the *actual* Naad realtime protocol.

This script is deliberately defensive: it never assumes an event shape. It logs
every frame received, classifies binary vs text, and reports handshake headers.
It stays within a single short session and sends no microphone audio, so spend
is minimal (connection-second metering only).

Usage:
    OOGAM_API_KEY=sk-setu-... python recon/scripts/phase0_ws_probe.py
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone

import websockets
from websockets.asyncio.client import connect as ws_connect

WS_URL = os.getenv("OOGAM_WS_URL", "wss://platform.oogam.ai/v1/realtime?v=2")
KEY = os.getenv("OOGAM_API_KEY", "")
MAX_TEXT_EVENTS = 40
LISTEN_SECONDS = 2.0


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def main() -> None:
    if not KEY:
        raise SystemExit("OOGAM_API_KEY must be set")

    events: list[dict] = []
    audio_chunks = 0
    audio_bytes = 0
    headers_seen: dict[str, str] = {}

    async with ws_connect(
        WS_URL,
        additional_headers={"Authorization": f"Bearer {KEY}"},
        open_timeout=20,
    ) as ws:
        # websockets 15 exposes handshake response headers on the protocol
        try:
            resp = ws.response
            for k, v in resp.headers.items():
                if k.lower().startswith("x-naad") or k.lower() in ("server", "date"):
                    headers_seen[k] = v
        except Exception as exc:  # defensive: header API varies by version
            headers_seen["_header_error"] = str(exc)

        start = time.monotonic()

        async def drain(seconds: float, label: str) -> None:
            nonlocal audio_chunks, audio_bytes
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                except websockets.ConnectionClosed as exc:
                    events.append({"t": now(), "type": "_CLOSED", "code": exc.code,
                                   "reason": exc.reason})
                    return
                if isinstance(msg, bytes):
                    audio_chunks += 1
                    audio_bytes += len(msg)
                    if audio_chunks <= 3:
                        events.append({"t": now(), "type": "_BINARY_AUDIO",
                                       "bytes": len(msg)})
                else:
                    try:
                        obj = json.loads(msg)
                    except json.JSONDecodeError:
                        obj = {"_raw": msg[:500]}
                    events.append({"t": now(), "type": "TEXT", "event": obj})
                    if len([e for e in events if e.get("type") == "TEXT"]) >= MAX_TEXT_EVENTS:
                        return

        async def send(obj: dict) -> None:
            events.append({"t": now(), "type": "SENT", "event": obj})
            await ws.send(json.dumps(obj))

        # 1) First server frame(s): capability advertisement / session.updated
        await drain(1.5, "greeting")
        # 2) Connection sequence from the PRD
        await send({"type": "set_lang", "value": "hi"})
        await drain(0.5, "after_set_lang")
        await send({"type": "set_voice", "voice": "f1"})
        await drain(0.8, "after_set_voice")
        await send({"type": "set_mode", "mode": "external_brain"})
        await drain(0.8, "after_set_mode")
        # 3) VAD configuration via session.update (v2)
        await send({"type": "session.update",
                    "session": {"vad_end_silence_ms": 700,
                                "input_audio_format": "pcm_16000",
                                "output_audio_format": "pcm_24000"}})
        await drain(0.8, "after_session_update")
        # 4) Streaming say: first chunk final:false, closing chunk final:true
        await send({"type": "say", "text": "नमस्ते, शर्मा क्लिनिक में आपका स्वागत है।",
                    "final": False, "lang": "hi"})
        await send({"type": "say", "text": "मैं आपकी क्या मदद कर सकता हूँ?", "final": True,
                    "lang": "hi"})
        await drain(3.0, "after_say")
        # 5) Barge-in primitive
        await send({"type": "stop_utterance"})
        await drain(1.0, "after_stop")
        elapsed = time.monotonic() - start

    report = {
        "captured_at": now(),
        "url": WS_URL,
        "elapsed_seconds": round(elapsed, 2),
        "handshake_headers": headers_seen,
        "audio_binary_chunks": audio_chunks,
        "audio_binary_bytes": audio_bytes,
        "events": events,
    }
    out = os.path.join(os.path.dirname(__file__), "..", "results", "phase0_ws_probe.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
