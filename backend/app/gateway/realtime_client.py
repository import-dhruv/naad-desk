"""Upstream Naad realtime WebSocket client.

Implements the *verified* connection sequence from docs/phase-0-findings.md and
a defensive parser that never assumes an event shape. The browser never talks to
this endpoint directly: the backend holds the API key.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

import websockets
from websockets.asyncio.client import connect as ws_connect

from ..config import settings
from ..logging_util import log

RETRYABLE_CODES = {1011, 1006, 1002}
WALLET_EMPTY = 4402


@dataclass
class ParsedEvent:
    kind: str            # "json" | "audio" | "closed"
    data: dict[str, Any] = field(default_factory=dict)
    audio: bytes = b""
    code: int | None = None
    reason: str = ""


def parse_frame(raw: Any) -> ParsedEvent:
    if isinstance(raw, bytes):
        return ParsedEvent(kind="audio", audio=raw)
    if isinstance(raw, str):
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                return ParsedEvent(kind="json", data=obj)
            return ParsedEvent(kind="json", data={"_raw": obj})
        except json.JSONDecodeError:
            return ParsedEvent(kind="json", data={"type": "_unparsed", "raw": raw[:300]})
    return ParsedEvent(kind="json", data={"type": "_unknown", "raw": str(raw)[:200]})


class RealtimeError(Exception):
    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class RealtimeClient:
    def __init__(self, call_id: str) -> None:
        self.call_id = call_id
        self.ws: Any = None
        self.capabilities: dict[str, Any] = {}
        self.limits: dict[str, Any] = {}
        self.connected = False

    async def connect(self) -> None:
        last: Exception | None = None
        for attempt, backoff in enumerate((0, *settings.reconnect_backoff_ms), start=1):
            if backoff:
                await asyncio.sleep(backoff / 1000)
            try:
                self.ws = await ws_connect(
                    settings.ws_url,
                    additional_headers=settings.auth_headers(),
                    open_timeout=20,
                    max_size=2**22,
                )
                self.connected = True
                log.info("upstream_connected", extra={"call_id": self.call_id, "attempt": attempt})
                return
            except Exception as exc:
                last = exc
                log.warning("upstream_connect_failed",
                            extra={"call_id": self.call_id, "attempt": attempt, "error": str(exc)})
        raise RealtimeError(f"realtime_connect_failed: {last}")

    async def send(self, obj: dict[str, Any]) -> None:
        if not self.connected or self.ws is None:
            raise RealtimeError("not connected")
        await self.ws.send(json.dumps(obj, ensure_ascii=False))

    async def events(self) -> AsyncIterator[ParsedEvent]:
        """Yield every upstream frame until the socket closes."""
        if self.ws is None:
            return
        try:
            async for raw in self.ws:
                parsed = parse_frame(raw)
                if parsed.kind == "json":
                    etype = parsed.data.get("type")
                    if etype == "session.updated":
                        self.capabilities = parsed.data.get("capabilities", {})
                        self.limits = parsed.data.get("limits", {})
                    if etype == "error":
                        code = parsed.data.get("code", "")
                        if code in ("language_at_capacity", "wallet_empty", "insufficient_credits"):
                            log.error("upstream_error", extra={"call_id": self.call_id, "code": code})
                            raise RealtimeError(str(parsed.data.get("detail", code)), code=code)
                yield parsed
        except websockets.ConnectionClosed as exc:
            self.connected = False
            if exc.code == WALLET_EMPTY:
                raise RealtimeError("wallet empty (4402)", code="wallet_empty") from exc
            yield ParsedEvent(kind="closed", code=exc.code, reason=exc.reason or "")
        finally:
            self.connected = False

    async def configure(self, language: str, voice: str) -> None:
        """Verified handshake: set_lang -> set_voice -> voice_ack -> set_mode ->
        mode_ack -> session.update VAD -> set_consent."""
        await self.send({"type": "set_lang", "value": language})
        await self.send({"type": "set_voice", "voice": voice})
        await self._wait_for("voice_ack", timeout=4.0)
        await self.send({"type": "set_mode", "mode": "external_brain"})
        await self._wait_for("mode_ack", timeout=4.0)
        await self.send({
            "type": "session.update",
            "session": {
                "vad_end_silence_ms": settings.vad_end_silence_ms,
                "input_audio_format": "pcm_16000",
                "output_audio_format": "pcm_24000",
            },
        })
        await self.send({"type": "set_consent", "training": False})

    async def _wait_for(self, event_type: str, timeout: float = 4.0) -> dict[str, Any]:
        """Consume frames until an ack arrives. Used only during handshake."""
        if self.ws is None:
            return {}
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            try:
                raw = await asyncio.wait_for(self.ws.recv(), timeout=deadline - asyncio.get_running_loop().time())
            except asyncio.TimeoutError:
                log.warning("ack_timeout", extra={"call_id": self.call_id, "event": event_type})
                return {}
            parsed = parse_frame(raw)
            if parsed.kind == "json" and parsed.data.get("type") == event_type:
                return parsed.data
        return {}

    async def say_chunks(self, chunks: list[str], language: str) -> None:
        for i, chunk in enumerate(chunks):
            await self.send({"type": "say", "text": chunk[:500],
                             "final": i == len(chunks) - 1, "lang": language})

    async def send_audio(self, pcm: bytes) -> None:
        """Forward one 20 ms frame of PCM16 16 kHz mono microphone audio."""
        if self.connected and self.ws is not None:
            await self.ws.send(pcm)

    async def stop_utterance(self) -> None:
        await self.send({"type": "stop_utterance"})

    async def close(self) -> None:
        if self.ws is not None:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None
        self.connected = False
