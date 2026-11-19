"""Schema validation, plan parsing and response composition tests."""
from __future__ import annotations

from app.orchestrator.response_composer import make_chunks, split_sentences, streaming_say_sequence
from app.schemas.events import ServerMessage
from app.schemas.tools import BookAppointmentArgs, TurnPlan


def test_turn_plan_valid():
    p = TurnPlan.model_validate({"intent": "BOOK_APPOINTMENT", "language": "Hinglish",
                                 "entities": {"doctor": "Mehta"}, "requested_tool": "book_appointment",
                                 "response_draft": "ok"})
    assert p.intent == "book_appointment"
    assert p.language == "hi"


def test_turn_plan_missing_fields_default():
    p = TurnPlan.model_validate({})
    assert p.intent == "faq"
    assert p.tool_args == {}


def test_tool_args_validation():
    a = BookAppointmentArgs.model_validate({"doctor": "Mehta", "confirmed": "false"})
    assert a.confirmed is False


def test_server_message():
    m = ServerMessage.model_validate({"type": "state", "payload": {"value": "listening"}})
    assert m.type == "state"


def test_sentence_splitting():
    text = "नमस्ते! आपका स्वागत है। मैं क्या मदद कर सकता हूँ?"
    sentences = split_sentences(text)
    assert len(sentences) >= 2


def test_chunks_under_limit():
    text = ". ".join(["This is a sentence with some words"] * 40)
    chunks = make_chunks(text)
    assert chunks
    assert all(len(c) <= 500 for c in chunks)
    frames = streaming_say_sequence(chunks)
    assert frames[-1]["final"] is True
    assert all(f["final"] is False for f in frames[:-1])
