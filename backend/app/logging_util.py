"""Structured JSON logging with per-call / per-turn context identifiers."""
from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any

call_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("call_id", default=None)
turn_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("turn_id", default=None)
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", record.getMessage()),
            "call_id": getattr(record, "call_id", call_id_var.get()),
            "turn_id": getattr(record, "turn_id", turn_id_var.get()),
            "request_id": getattr(record, "request_id", request_id_var.get()),
            "component": getattr(record, "component", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "status": getattr(record, "status", None),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Attach any extra structured fields passed via `extra={...}`.
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "taskName", "message", "event", "call_id",
                "turn_id", "request_id", "component", "duration_ms", "status",
            }:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    from .config import settings
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    return logger


log = get_logger("naad-desk")


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


class Timer:
    """Context manager that logs a duration under a named event."""

    def __init__(self, event: str, logger: logging.Logger | None = None, **fields: Any) -> None:
        self.event = event
        self.logger = logger or log
        self.fields = fields
        self.start = 0.0

    def __enter__(self) -> "Timer":
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        duration_ms = round((time.perf_counter() - self.start) * 1000, 2)
        self.logger.info(
            self.event,
            extra={"event": self.event, "duration_ms": duration_ms,
                   "status": "error" if exc_type else "ok", **self.fields},
        )
