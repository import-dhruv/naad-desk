"""Per-call session: bridges browser WebSocket <-> upstream realtime socket.

Owns conversation state, dual-channel recording, latency instrumentation and
barge-in cancellation. Each call is fully independent.
"""
from __future__ import annotations

import asyncio
import base64
import os
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import ROOT, settings
from ..db.database import SessionLocal
from ..db.models import Call
from ..logging_util import call_id_var, log
from ..orchestrator.engine import process_turn
from ..orchestrator.guardrails import disclosure
from ..orchestrator.state import ConversationState
from ..retrieval.hybrid import HybridRetriever
from .realtime_client import RealtimeClient, RealtimeError

RECORDINGS = (
    Path(os.getenv("RECORDINGS_DIR", "/tmp/naad-recordings"))
    if settings.is_vercel else ROOT / "recordings"
)


def _write_wav(path: Path, frames: list[bytes], sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(b"".join(frames))


class CallSession:
    def __init__(self, call_id: str, language: str = "hi", voice: str | None = None,
                 retriever: HybridRetriever | None = None, outgoing=None) -> None:
        self.call_id = call_id
        self.state = ConversationState(call_id=call_id, language=language,
                                       voice=voice or settings.voice)
        self.retriever = retriever or HybridRetriever()
        self.outgoing = outgoing          # async callable(dict) -> None
        self.upstream = RealtimeClient(call_id)
        self.caller_frames: list[bytes] = []
        self.agent_frames: list[bytes] = []
        self.started = time.monotonic()
        self.ended = False
        self._upstream_task: asyncio.Task | None = None
        self._busy = False
        self._token = call_id_var.set(call_id)
        self._greeted = False

    async def emit(self, msg_type: str, payload: dict[str, Any] | None = None, **extra) -> None:
        msg = {"type": msg_type, "call_id": self.call_id, "ts": time.monotonic(),
               "payload": payload or {}, **extra}
        if self.outgoing:
            await self.outgoing(msg)

    async def start(self) -> None:
        db = SessionLocal()
        try:
            call = db.get(Call, self.call_id)
            if call is None:
                db.add(Call(id=self.call_id, language=self.state.language,
                            prompt_version=self.state.prompt_version,
                            kb_version=self.state.kb_version))
                db.commit()
        finally:
            db.close()

        await self.upstream.connect()
        await self.upstream.configure(self.state.language, self.state.voice)
        await self.emit("session.ready", {"protocol": 1, "voice": self.state.voice,
                                          "language": self.state.language})
        notice = disclosure(self.state.language)
        await self.emit("recording.notice", {"text": notice})
        greeting = (
            "નમસ્તે, શર્મા ક્લિનિકમાં આપનું સ્વાગત છે. " + notice + " હું આપની શું મદદ કરી શકું?"
            if self.state.language == "gu" else
            "नमस्ते, शर्मा क्लिनिक में आपका स्वागत है। " + notice + " मैं आपकी क्या मदद कर सकता हूँ?"
            if self.state.language == "hi" else
            "Welcome to Sharma Clinic. " + notice + " How can I help you today?"
        )
        await self.emit("caption", {"speaker": "agent", "text": greeting, "final": True})
        await self.upstream.say_chunks([greeting], self.state.language)
        self._greeted = True
        self._upstream_task = asyncio.create_task(self._pump_upstream())

    async def _pump_upstream(self) -> None:
        try:
            async for event in self.upstream.events():
                if self.ended:
                    break
                if event.kind == "audio":
                    self.agent_frames.append(event.audio)
                    await self.emit("audio", {"data": base64.b64encode(event.audio).decode(),
                                              "sample_rate": 24000})
                elif event.kind == "json":
                    etype = event.data.get("type")
                    if etype == "state":
                        await self.emit("state", {"value": event.data.get("value")})
                    elif etype == "stt":
                        # The engine can emit partial STT updates (final:false /
                        # replace:true). Only endpointed transcripts may trigger
                        # a full Sutra + retrieval + say cycle.
                        if event.data.get("final") is False:
                            continue
                        text = event.data.get("text") or event.data.get("transcript", "")
                        if text and not self._busy and text != getattr(self, "_last_stt", ""):
                            self._last_stt = text
                            await self._handle_transcript(text)
                    elif etype in ("interrupted", "error") and etype == "interrupted":
                        await self.emit("stop_playback", {"reason": "barge_in"})
                        await self.upstream.stop_utterance()
                elif event.kind == "closed":
                    await self.emit("error", {"detail": f"upstream closed: {event.code}"})
                    break
        except RealtimeError as exc:
            await self.emit("error", {"detail": str(exc), "code": exc.code})
        except Exception as exc:
            log.exception("upstream_pump_failed", extra={"call_id": self.call_id})
            await self.emit("error", {"detail": str(exc)})

    async def _handle_transcript(self, text: str) -> None:
        self._busy = True
        t_start = time.monotonic()
        try:
            await self.emit("caption", {"speaker": "caller", "text": text, "final": True})
            db = SessionLocal()
            try:
                result = await process_turn(db, self.retriever, self.state, text, self.call_id)
            finally:
                db.close()
            await self.emit("caption", {"speaker": "agent", "text": result.caption, "final": True})
            await self.emit("timing", result.timings)
            if result.tool_results:
                await self.emit("tool", {"calls": result.tool_results})
            if result.retrieval:
                await self.emit("retrieval", result.retrieval)
            if result.spoken_chunks:
                await self.upstream.say_chunks(result.spoken_chunks, result.language)
                await self.emit("timing", {"first_say_ms": round((time.monotonic() - t_start) * 1000, 2)})
            if result.handoff:
                await self.emit("state", {"value": "handoff"})
        finally:
            self._busy = False

    async def handle_message(self, msg: dict[str, Any]) -> None:
        mtype = msg.get("type")
        if mtype == "audio":
            data = msg.get("data", "")
            try:
                pcm = base64.b64decode(data)
            except Exception:
                return
            self.caller_frames.append(pcm)
            await self.upstream.send_audio(pcm)
        elif mtype == "text_input":
            # Used by the automated 24-scenario replay runner.
            if not self._busy:
                await self._handle_transcript(msg.get("text", ""))
        elif mtype == "interrupt":
            await self.upstream.stop_utterance()
            await self.emit("stop_playback", {"reason": "caller"})
        elif mtype == "set_lang":
            lang = msg.get("language", "hi")
            self.state.language = lang
            await self.upstream.send({"type": "set_lang", "value": lang})
        elif mtype == "ping":
            await self.emit("pong", {})

    async def end(self, reason: str = "caller_hangup") -> None:
        if self.ended:
            return
        self.ended = True
        _write_wav(RECORDINGS / self.call_id / "caller.wav", self.caller_frames, 16000)
        _write_wav(RECORDINGS / self.call_id / "agent.wav", self.agent_frames, 24000)
        try:
            await self.upstream.stop_utterance()
        except Exception:
            pass
        await self.upstream.close()
        if self._upstream_task:
            self._upstream_task.cancel()
        duration = time.monotonic() - self.started
        db = SessionLocal()
        try:
            call = db.get(Call, self.call_id)
            if call:
                call.ended_at = datetime.now(timezone.utc)
                call.outcome = "completed" if not self.state.safety_events else "safety_escalation"
                call.cost_paise = int(self.state.cost_paise)
                call.language = self.state.language
                db.commit()
        finally:
            db.close()
        await self.emit("call.ended", {"reason": reason, "duration_seconds": round(duration, 2)})
        call_id_var.reset(self._token)

    # Backward-compatible alias used by tests and the gateway.
    send_audio = None
