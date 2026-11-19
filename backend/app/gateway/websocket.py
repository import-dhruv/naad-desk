"""Browser WebSocket endpoint (WS /ws/call).

Protocol is documented in schemas/events.py. The API key never reaches the
browser: the backend owns the upstream realtime connection.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..logging_util import log
from ..retrieval.hybrid import HybridRetriever
from .session import CallSession

router = APIRouter()

# Shared retriever avoids re-embedding on every call. Built lazily on first use.
_shared_retriever: HybridRetriever | None = None


def get_retriever() -> HybridRetriever:
    global _shared_retriever
    if _shared_retriever is None:
        from ..db.database import SessionLocal
        _shared_retriever = HybridRetriever()
        db = SessionLocal()
        try:
            _shared_retriever.build_from_db(db)
        finally:
            db.close()
    return _shared_retriever


def set_retriever(retriever: HybridRetriever) -> None:
    global _shared_retriever
    _shared_retriever = retriever


@router.websocket("/ws/call")
async def call_socket(ws: WebSocket) -> None:
    await ws.accept()
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    session: CallSession | None = None

    async def sender() -> None:
        while True:
            msg = await queue.get()
            if msg is None:  # sentinel: flush complete
                break
            await ws.send_json(msg)

    sender_task = asyncio.create_task(sender())

    async def emit(msg: dict[str, Any]) -> None:
        await queue.put(msg)

    async def stop_sender() -> None:
        await queue.put(None)
        try:
            await asyncio.wait_for(sender_task, timeout=3.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass

    try:
        # First frame must be `start`.
        raw = await ws.receive_text()
        start = json.loads(raw)
        if start.get("type") != "start":
            await emit({"type": "error", "payload": {"detail": "expected start frame"}})
            return
        call_id = f"call-{uuid.uuid4().hex[:12]}"
        session = CallSession(
            call_id=call_id,
            language=start.get("language", "hi"),
            voice=start.get("voice"),
            retriever=get_retriever(),
            outgoing=emit,
        )
        await session.start()

        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await emit({"type": "error", "payload": {"detail": "invalid JSON"}})
                continue
            mtype = msg.get("type")
            if mtype == "end":
                await session.end(reason=msg.get("reason", "caller_hangup"))
                break
            await session.handle_message(msg)
    except WebSocketDisconnect:
        log.info("browser_disconnected", extra={"call_id": session.call_id if session else None})
    except Exception as exc:
        log.exception("call_socket_error")
        await emit({"type": "error", "payload": {"detail": str(exc)}})
    finally:
        if session and not session.ended:
            await session.end(reason="socket_closed")
        await stop_sender()
