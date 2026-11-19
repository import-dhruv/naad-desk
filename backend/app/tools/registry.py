"""Tool dispatcher with typed argument parsing and execution timing."""
from __future__ import annotations

import time
from typing import Any

from sqlalchemy.orm import Session

from ..schemas.tools import (
    BookAppointmentArgs,
    CancelArgs,
    FeesArgs,
    HandoffArgs,
    RescheduleArgs,
    SearchAvailabilityArgs,
    ToolResult,
)
from .availability import search_availability
from .booking import book_appointment
from .cancellation import cancel_appointment
from .fees import get_fees
from .handoff import handoff_to_human
from .rescheduling import reschedule_appointment

PARSERS = {
    "search_availability": SearchAvailabilityArgs,
    "book_appointment": BookAppointmentArgs,
    "reschedule_appointment": RescheduleArgs,
    "cancel_appointment": CancelArgs,
    "get_fees": FeesArgs,
    "handoff_to_human": HandoffArgs,
}


def execute_tool(name: str, args: dict[str, Any], db: Session, call_id: str,
                 language: str = "hi", caller_confirmed: bool = False) -> ToolResult:
    start = time.perf_counter()
    parser = PARSERS.get(name)
    if parser is None:
        return ToolResult(ok=False, tool=name, error=f"Unknown tool: {name}")
    try:
        typed = parser.model_validate(args or {})
    except Exception as exc:
        return ToolResult(ok=False, tool=name, error=f"Invalid tool arguments: {exc}")

    if name == "search_availability":
        result = search_availability(db, typed.doctor, typed.date, typed.part_of_day or "any", language)
    elif name == "book_appointment":
        result = book_appointment(db, call_id, typed, language, caller_confirmed)
    elif name == "reschedule_appointment":
        result = reschedule_appointment(db, call_id, typed, language, caller_confirmed)
    elif name == "cancel_appointment":
        result = cancel_appointment(db, call_id, typed, language, caller_confirmed)
    elif name == "get_fees":
        result = get_fees(db, typed, language)
    else:
        result = handoff_to_human(typed, language)

    # Attach execution time for the per-call latency waterfall.
    data = dict(result.data)
    if result.error:
        data["error"] = result.error
    data["_execution_time_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return ToolResult(ok=result.ok, tool=result.tool, data=data,
                      spoken=result.spoken, error=result.error)
