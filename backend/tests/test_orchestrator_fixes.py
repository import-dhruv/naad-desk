"""Regression tests for orchestration fixes (issues #4, #6)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.models import Call, ToolCall, Turn  # noqa: E402
from app.orchestrator.engine import process_turn  # noqa: E402
from app.orchestrator.state import ConversationState  # noqa: E402
from app.retrieval.hybrid import HybridRetriever  # noqa: E402


async def _plan(**overrides):
    plan = {"intent": "faq", "language": "hi", "entities": {},
            "requested_tool": None, "tool_args": {}, "response_draft": "ठीक है।",
            "grounded_answer": "", "clarification": None}
    plan.update(overrides)
    return plan


@pytest.mark.asyncio
async def test_caller_and_agent_turns_are_persisted(db, monkeypatch):
    async def fake_chat(*args, **kwargs):
        return await _plan()

    monkeypatch.setattr("app.orchestrator.engine.oogam.chat_json", fake_chat)
    db.add(Call(id="issue4"))
    db.commit()
    retriever = HybridRetriever(prefer_real=False)
    retriever.build([])
    state = ConversationState(call_id="issue4")

    await process_turn(db, retriever, state, "नमस्ते, क्या आप बात कर रहे हैं?", "issue4")

    speakers = [t.speaker for t in db.query(Turn).filter(Turn.call_id == "issue4").all()]
    assert "caller" in speakers
    assert "agent" in speakers


@pytest.mark.asyncio
async def test_ambiguous_date_does_not_execute_tool(db, monkeypatch):
    async def fake_chat(*args, **kwargs):
        return await _plan(intent="booking", requested_tool="search_availability",
                           tool_args={"date": "शुक्रवार"}, response_draft="")

    monkeypatch.setattr("app.orchestrator.engine.oogam.chat_json", fake_chat)
    db.add(Call(id="issue6"))
    db.commit()
    retriever = HybridRetriever(prefer_real=False)
    retriever.build([])
    state = ConversationState(call_id="issue6")

    result = await process_turn(db, retriever, state, "शुक्रवार को अपॉइंटमेंट चाहिए", "issue6")

    assert result.tool_results == []
    assert db.query(ToolCall).join(Turn).filter(Turn.call_id == "issue6").count() == 0
    assert "स्पष्ट" in result.caption
