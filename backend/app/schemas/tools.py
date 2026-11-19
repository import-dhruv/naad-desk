"""Typed schemas for deterministic business tools and the LLM turn plan (§6.2, §8)."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ToolName(str, Enum):
    SEARCH_AVAILABILITY = "search_availability"
    BOOK_APPOINTMENT = "book_appointment"
    RESCHEDULE_APPOINTMENT = "reschedule_appointment"
    CANCEL_APPOINTMENT = "cancel_appointment"
    GET_FEES = "get_fees"
    HANDOFF_TO_HUMAN = "handoff_to_human"


class ToolResult(BaseModel):
    ok: bool
    tool: str
    data: dict[str, Any] = Field(default_factory=dict)
    # Deterministic, fully-formed spoken text injected verbatim (§8.4).
    spoken: str = ""
    error: str | None = None


class SearchAvailabilityArgs(BaseModel):
    doctor: str | None = None
    date: str | None = None       # ISO YYYY-MM-DD after resolution
    part_of_day: str | None = None  # morning|afternoon|evening|any


class BookAppointmentArgs(BaseModel):
    doctor: str | None = None
    date: str | None = None
    time: str | None = None       # HH:MM
    slot_id: int | None = None
    patient_name: str | None = None
    phone: str | None = None
    confirmed: bool = False
    confirm_token: str | None = None


class RescheduleArgs(BaseModel):
    phone: str | None = None
    appointment_ref: str | None = None
    new_slot_id: int | None = None
    new_date: str | None = None
    new_time: str | None = None
    confirmed: bool = False
    confirm_token: str | None = None


class CancelArgs(BaseModel):
    phone: str | None = None
    appointment_ref: str | None = None
    confirmed: bool = False
    confirm_token: str | None = None


class FeesArgs(BaseModel):
    doctor: str | None = None


class HandoffArgs(BaseModel):
    reason: str = "caller_request"


class TurnPlan(BaseModel):
    """Structured output requested from Sutra — no raw numbers authored by the LLM."""
    intent: str = "faq"
    language: str = "hi"
    entities: dict[str, Any] = Field(default_factory=dict)
    requested_tool: str | None = None
    tool_args: dict[str, Any] = Field(default_factory=dict)
    needs_confirmation: bool = False
    clarification: str | None = None
    safety_event: str | None = None
    response_draft: str = ""
    grounded_answer: str = ""

    @field_validator("intent")
    @classmethod
    def normalize_intent(cls, value: str) -> str:
        return (value or "faq").strip().lower().replace(" ", "_")

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        value = (value or "hi").strip().lower()
        return {"hinglish": "hi", "english": "en-in", "indian_english": "en-in",
                "hindi": "hi", "gujarati": "gu"}.get(value, value)
