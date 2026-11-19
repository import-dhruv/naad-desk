"""Versioned browser<->gateway WebSocket message protocol (PRD §14).

Every client message has `v` (protocol version) and `type`. Server messages carry
`type`, optional `call_id`, and a `ts` monotonic timestamp. Pydantic validates the
shape; unknown types are rejected with an `error` frame rather than crashing.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ClientMsgType(str, Enum):
    START = "start"
    AUDIO = "audio"
    END = "end"
    STOP_PLAYBACK = "stop_playback"
    INTERRUPT = "interrupt"
    SET_LANG = "set_lang"
    TEXT_INPUT = "text_input"   # useful for automated scenario replay
    PING = "ping"


class ServerMsgType(str, Enum):
    SESSION_READY = "session.ready"
    STATE = "state"
    CAPTION = "caption"
    TURN = "turn"
    TIMING = "timing"
    TOOL = "tool"
    RETRIEVAL = "retrieval"
    COST = "cost"
    ERROR = "error"
    PONG = "pong"
    CALL_ENDED = "call.ended"
    RECORDING_NOTICE = "recording.notice"


class StartMsg(BaseModel):
    v: int = 1
    type: Literal["start"] = "start"
    language: str = "hi"
    voice: str | None = None
    disclosure_ack: bool = True


class AudioMsg(BaseModel):
    v: int = 1
    type: Literal["audio"] = "audio"
    # base64-encoded PCM16 16 kHz mono frames
    data: str
    seq: int = 0


class TextInputMsg(BaseModel):
    v: int = 1
    type: Literal["text_input"] = "text_input"
    text: str
    language: str | None = None
    final: bool = True


class ControlMsg(BaseModel):
    v: int = 1
    type: Literal["end"] | Literal["stop_playback"] | Literal["interrupt"] | Literal["ping"]
    reason: str | None = None


class SetLangMsg(BaseModel):
    v: int = 1
    type: Literal["set_lang"] = "set_lang"
    language: str


class ServerMessage(BaseModel):
    type: str
    call_id: str | None = None
    ts: float = 0.0
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        return value
