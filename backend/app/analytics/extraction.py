"""Structured call extraction with Sutra JSON output and one schema retry (§10.3)."""
from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError

from ..gateway.oogam_client import oogam

SYSTEM = """Extract structured information from this clinic call transcript. Output ONE JSON object only.
Never invent facts. If something is not mentioned, use null or empty values.
Shape:
{
 "call_id": string,
 "primary_language": string,
 "language_switches": [string],
 "caller_goal": string,
 "goal_achieved": boolean|null,
 "appointment": object|null,
 "faq_topics": [string],
 "handoff_requested": boolean,
 "safety_events": [string],
 "unanswered_questions": [string],
 "caller_sentiment": string,
 "summary_bullets": [string]
}
"""


class Extraction(BaseModel):
    call_id: str = ""
    primary_language: str = "hi"
    language_switches: list[str] = Field(default_factory=list)
    caller_goal: str = ""
    goal_achieved: bool | None = None
    appointment: dict = Field(default_factory=dict)
    faq_topics: list[str] = Field(default_factory=list)
    handoff_requested: bool = False
    safety_events: list[str] = Field(default_factory=list)
    unanswered_questions: list[str] = Field(default_factory=list)
    caller_sentiment: str = "neutral"
    summary_bullets: list[str] = Field(default_factory=list)


async def extract(transcript: str, call_id: str) -> Extraction:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"CALL_ID: {call_id}\nTRANSCRIPT:\n{transcript}"},
    ]
    for attempt in range(2):
        raw = await oogam.chat_json(messages, call_id=call_id)
        try:
            return Extraction.model_validate(raw)
        except ValidationError:
            messages.append({"role": "user", "content": "The previous JSON was invalid. Return valid JSON only."})
    return Extraction(call_id=call_id)
