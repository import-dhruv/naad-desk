"""Cross-dialect write serialization for appointment transactions.

SQLite uses BEGIN IMMEDIATE; Postgres uses SELECT ... FOR UPDATE. Both prevent
two concurrent callers from booking the same slot.
"""
from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session


def lock_for_update(db: Session, model, row_id: int) -> None:
    dialect = db.get_bind().dialect.name
    if dialect == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))
    else:
        db.execute(select(model).where(model.id == row_id).with_for_update())
