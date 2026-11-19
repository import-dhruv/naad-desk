"""Short-lived, in-process confirmation tokens (§8.1).

The confirmation rule lives in backend code: no booking/reschedule/cancel is
committed unless the caller explicitly confirms with a token minted by a prior
read-back step. The token is stored server-side and injected by the orchestrator
when it detects an affirmative reply — never authored by the LLM.
"""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Any

TTL_SECONDS = 300


@dataclass
class Pending:
    kind: str
    payload: dict[str, Any]
    token: str
    created_at: float = field(default_factory=time.time)


_STORE: dict[str, Pending] = {}


def mint(call_id: str, kind: str, payload: dict[str, Any]) -> str:
    token = secrets.token_urlsafe(8)
    _STORE[call_id] = Pending(kind=kind, payload=payload, token=token)
    return token


def peek(call_id: str) -> Pending | None:
    pending = _STORE.get(call_id)
    if not pending:
        return None
    if time.time() - pending.created_at > TTL_SECONDS:
        _STORE.pop(call_id, None)
        return None
    return pending


def consume(call_id: str, token: str | None, kind: str) -> dict[str, Any] | None:
    pending = peek(call_id)
    if not pending or pending.kind != kind:
        return None
    if token and token != pending.token:
        return None
    _STORE.pop(call_id, None)
    return pending.payload


def clear(call_id: str) -> None:
    _STORE.pop(call_id, None)
