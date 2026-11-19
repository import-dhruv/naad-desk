"""Human handoff tool (§8, §9)."""
from __future__ import annotations

from ..schemas.tools import HandoffArgs, ToolResult


def handoff_to_human(args: HandoffArgs, language: str = "hi") -> ToolResult:
    reason = args.reason or "caller_request"
    if language == "gu":
        spoken = "હું તમને હમણાં જ માનવ એજન્ટ સાથે જોડું છું. કૃપા કરીને થોડીવાર રાહ જુઓ."
    elif language == "hi":
        spoken = "मैं आपको अभी एक मानव एजेंट से जोड़ता हूँ. कृपया थोड़ा इंतज़ार करें."
    else:
        spoken = "I'm connecting you with a human agent now. Please hold for a moment."
    return ToolResult(ok=True, tool="handoff_to_human",
                      data={"handoff": True, "reason": reason, "queue": "reception"},
                      spoken=spoken)
