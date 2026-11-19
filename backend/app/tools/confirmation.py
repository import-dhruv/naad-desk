"""Short-lived confirmation tokens stored in the database (§8.1).

DB-backed so a token minted by one Vercel function instance can be consumed by
another (after a WebSocket reconnect or instance switch).
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from ..db.models import PendingConfirmation

TTL_SECONDS = 300


@dataclass
class Pending:
    kind: str
    payload: dict[str, Any]
    token: str
    created_at: float


def _row(db: Session, call_id: str) -> PendingConfirmation | None:
    return db.get(PendingConfirmation, call_id)


def mint(db: Session, call_id: str, kind: str, payload: dict[str, Any]) -> str:
    import json
    token = secrets.token_urlsafe(8)
    row = _row(db, call_id)
    if row is None:
        db.add(PendingConfirmation(call_id=call_id, kind=kind, token=token,
                                   created_at=datetime.now(timezone.utc),
                                   payload_json=json.dumps(payload, ensure_ascii=False)))
    else:
        row.kind, row.token = kind, token
        row.payload_json = json.dumps(payload, ensure_ascii=False)
        row.created_at = datetime.now(timezone.utc)
    db.commit()
    return token


def peek(db: Session, call_id: str) -> Pending | None:
    import json
    row = _row(db, call_id)
    if not row:
        return None
    created = row.created_at
    if created.tzinfo is None:  # SQLite returns naive UTC for TZDateTime
        created = created.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - created).total_seconds()
    if age > TTL_SECONDS:
        db.delete(row)
        db.commit()
        return None
    return Pending(kind=row.kind, payload=json.loads(row.payload_json or "{}"),
                   token=row.token, created_at=created.timestamp())


def consume(db: Session, call_id: str, token: str | None, kind: str) -> dict[str, Any] | None:
    pending = peek(db, call_id)
    if not pending or pending.kind != kind:
        return None
    if token and token != pending.token:
        return None
    row = _row(db, call_id)
    if row:
        db.delete(row)
        db.commit()
    return pending.payload


def clear(db: Session, call_id: str) -> None:
    row = _row(db, call_id)
    if row:
        db.delete(row)
        db.commit()
