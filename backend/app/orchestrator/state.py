"""Per-call conversation state (§6)."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationState:
    call_id: str
    language: str = "hi"
    voice: str = "f1"
    history: list[dict[str, str]] = field(default_factory=list)
    current_intent: str = "greeting"
    patient_name: str | None = None
    phone_number: str | None = None
    selected_doctor: str | None = None
    requested_date: str | None = None
    requested_time: str | None = None
    appointment_status: str = "none"
    pending_confirmation: str | None = None   # tool name awaiting a yes
    pending_token: str | None = None
    previous_tool_results: list[dict[str, Any]] = field(default_factory=list)
    retrieved_knowledge: list[str] = field(default_factory=list)
    retrieval_confidence: float = 0.0
    prompt_version: str = "v1.0"
    kb_version: str = "kb-v1"
    turn_index: int = 0
    started_at: float = field(default_factory=time.monotonic)
    safety_events: list[str] = field(default_factory=list)
    handoff_requested: bool = False
    current_stage: str = "idle"
    timings: dict[str, float] = field(default_factory=dict)
    cost_paise: float = 0.0
    interrupted: bool = False

    def add_turn(self, speaker: str, text: str, language: str | None = None) -> None:
        self.turn_index += 1
        self.history.append({"idx": str(self.turn_index), "speaker": speaker,
                             "text": text, "language": language or self.language})

    RESUME_FIELDS = (
        "language", "voice", "current_intent", "patient_name", "phone_number",
        "selected_doctor", "requested_date", "requested_time", "appointment_status",
        "pending_confirmation", "pending_token", "retrieval_confidence",
        "turn_index", "safety_events", "handoff_requested", "cost_paise",
    )

    def to_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.RESUME_FIELDS}

    @classmethod
    def from_dict(cls, call_id: str, data: dict[str, Any]) -> "ConversationState":
        state = cls(call_id=call_id)
        for key in cls.RESUME_FIELDS:
            if key in data and data[key] is not None:
                setattr(state, key, data[key])
        return state

    def snapshot(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id, "language": self.language,
            "current_intent": self.current_intent, "patient_name": self.patient_name,
            "selected_doctor": self.selected_doctor, "requested_date": self.requested_date,
            "requested_time": self.requested_time, "appointment_status": self.appointment_status,
            "pending_confirmation": self.pending_confirmation,
            "retrieval_confidence": self.retrieval_confidence,
            "safety_events": self.safety_events, "turns": len(self.history),
        }
