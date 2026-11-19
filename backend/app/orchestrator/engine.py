"""Conversation orchestrator: one structured Sutra plan per turn, retrieval,
deterministic tools and exact-figure injection (§6)."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from ..gateway.oogam_client import oogam
from ..logging_util import log
from ..retrieval.hybrid import HybridRetriever
from ..schemas.tools import TurnPlan
from ..tools.booking import is_affirmative
from ..tools.date_resolver import resolve_date
from ..tools.registry import execute_tool
from . import guardrails
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .response_composer import make_chunks
from .state import ConversationState

LANG_CODES = {"hi": "hi", "gu": "gu", "en": "en-in", "en-in": "en-in",
              "hinglish": "hi", "english": "en-in", "indian_english": "en-in"}


@dataclass
class TurnResult:
    spoken_chunks: list[str] = field(default_factory=list)
    caption: str = ""
    language: str = "hi"
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    retrieval: dict[str, Any] = field(default_factory=dict)
    timings: dict[str, float] = field(default_factory=dict)
    safety_event: str | None = None
    handoff: bool = False
    state_updates: dict[str, Any] = field(default_factory=dict)


def _is_iso_date(value: str) -> bool:
    import re
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)))


def detect_language(text: str, state: ConversationState) -> str:
    """Script-based hint; the LLM plan can override."""
    dev = sum("\u0900" <= c <= "\u097f" for c in text)
    guj = sum("\u0a80" <= c <= "\u0aff" for c in text)
    if guj > 3 and guj >= dev:
        return "gu"
    if dev > 3:
        return "hi"
    return state.language if state.language in ("hi", "gu", "en-in") else "hi"


async def process_turn(db: Session, retriever: HybridRetriever, state: ConversationState,
                       transcript: str, call_id: str) -> TurnResult:
    result = TurnResult(language=detect_language(transcript, state))
    t0 = time.perf_counter()
    state.add_turn("caller", transcript, result.language)
    state.current_stage = "planning"

    # --- Guardrails: caller input is untrusted. ---
    guard = guardrails.guard(transcript, result.language, source="caller")
    if guard.action == "emergency":
        state.safety_events.append(guard.reason)
        result.safety_event = guard.reason
        result.handoff = True
        result.spoken_chunks = make_chunks(guard.spoken)
        result.caption = guard.spoken
        result.state_updates = {"safety_event": guard.reason, "handoff": True}
        return _finalize(result, state, t0, db)
    if guard.action == "refuse_medical":
        result.spoken_chunks = make_chunks(guard.spoken)
        result.caption = guard.spoken
        result.safety_event = guard.reason
        result.state_updates = {"safety_event": guard.reason}
        return _finalize(result, state, t0, db)
    if guard.action == "injection_blocked":
        log.warning("injection_blocked", extra={"call_id": call_id})
        result.caption = transcript
        result.spoken_chunks = make_chunks(
            "मैं इस निर्देश को नहीं मान सकता। कृपया शर्मा क्लिनिक से संबंधित प्रश्न पूछें।"
            if result.language == "hi" else "I can't follow that instruction. Please ask about Sharma Clinic.")
        return _finalize(result, state, t0, db)

    # --- State updates from raw speech (deterministic, no LLM invention). ---
    _extract_entities_from_speech(transcript, state)

    # --- Retrieval (only for informational turns). ---
    retrieval_start = time.perf_counter()
    retrieval = retriever.query(transcript, hinglish=True)
    result.retrieval = {
        "confidence": retrieval.confidence,
        "grounded": retrieval.grounded,
        "chunks": [{"id": c.chunk_id, "section": c.section, "language": c.language,
                    "content": c.content[:300]} for c in retrieval.chunks],
        "backend": retrieval.backend,
        "execution_time_ms": retrieval.execution_time_ms,
    }
    state.retrieved_knowledge = [c.chunk_id for c in retrieval.chunks]
    state.retrieval_confidence = retrieval.confidence
    result.timings["retrieval_ms"] = round((time.perf_counter() - retrieval_start) * 1000, 2)

    # --- Structured plan from Sutra. ---
    plan_start = time.perf_counter()
    plan_raw = await oogam.chat_json(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(
                transcript, state.snapshot(),
                [{"id": c.chunk_id, "section": c.section, "content": c.content[:500]}
                 for c in retrieval.chunks],
                guardrail_note=("Caller affirmed a pending read-back" if
                                state.pending_confirmation and is_affirmative(transcript) else ""),
            )},
        ],
        call_id=call_id,
    )
    try:
        plan = TurnPlan.model_validate(plan_raw)
    except Exception:
        plan = TurnPlan(intent="faq", clarification="कृपया दोबारा कहें।")
    result.timings["plan_ms"] = round((time.perf_counter() - plan_start) * 1000, 2)
    if plan.language in LANG_CODES:
        result.language = LANG_CODES[plan.language]
    state.current_intent = plan.intent

    # Retrieved documents are untrusted: scan them too.
    for chunk in retrieval.chunks:
        if guardrails.check_injection(chunk.content):
            log.warning("retrieved_injection_ignored", extra={"call_id": call_id,
                                                               "chunk": chunk.chunk_id})

    # --- Affirmation -> convert to a confirmed tool call. ---
    caller_confirmed = bool(state.pending_confirmation and is_affirmative(transcript))
    requested_tool = plan.requested_tool
    tool_args = dict(plan.tool_args or {})
    if caller_confirmed:
        requested_tool = state.pending_confirmation
        tool_args["confirmed"] = True
        tool_args["confirm_token"] = state.pending_token
    if plan.needs_confirmation and not state.pending_confirmation:
        # There is no read-back awaiting confirmation. Ignore the model's flag
        # rather than escalating: the backend owns the confirmation state.
        plan.needs_confirmation = False

    # Resolve natural-language dates to ISO before any tool sees them (§8.5).
    for key in ("date", "new_date"):
        value = tool_args.get(key)
        if value and not _is_iso_date(value):
            resolution = resolve_date(str(value))
            if resolution.iso and not resolution.ambiguous:
                tool_args[key] = resolution.iso
            else:
                tool_args.pop(key, None)
                if resolution.ambiguous:
                    plan.clarification = plan.clarification or (
                        "कृपया स्पष्ट तारीख़ बताएँ।" if result.language == "hi"
                        else "Please specify the exact date."
                    )

    # --- Tool execution. ---
    if requested_tool:
        tool_start = time.perf_counter()
        tool_result = execute_tool(requested_tool, tool_args, db, call_id,
                                   result.language, caller_confirmed)
        result.timings["tool_ms"] = round((time.perf_counter() - tool_start) * 1000, 2)
        result.tool_results.append({
            "name": requested_tool, "args": tool_args,
            "ok": tool_result.ok, "error": tool_result.error,
            "data": tool_result.data,
        })
        state.previous_tool_results.append(result.tool_results[-1])
        if tool_result.data.get("phase") == "pending_confirmation":
            state.pending_confirmation = requested_tool
            state.pending_token = tool_result.data.get("confirm_token")
        else:
            state.pending_confirmation = None
            state.pending_token = None
        if not tool_result.ok:
            # Fall back to a clarification rather than inventing a result.
            result.spoken_chunks = make_chunks(
                "माफ़ी, मैं यह पुष्टि नहीं कर पा रहा। कृपया दोबारा कहें या मानव एजेंट से बात करें।"
                if result.language == "hi" else "Sorry, I couldn't complete that. Please repeat or speak to a human agent.")
            result.caption = result.spoken_chunks[0]
            return _finalize(result, state, t0, db)
        if tool_result.spoken:
            # Deterministic spoken text with exact DB figures — never LLM-authored.
            result.spoken_chunks = make_chunks(tool_result.spoken)
            result.caption = tool_result.spoken
            if requested_tool == "handoff_to_human":
                result.handoff = True
            return _finalize(result, state, t0, db)

    # --- Grounded FAQ / smalltalk response. ---
    if plan.clarification:
        spoken = plan.clarification
    elif plan.grounded_answer and retrieval.grounded:
        spoken = plan.grounded_answer
    elif plan.response_draft and plan.intent in ("smalltalk", "faq", "other"):
        spoken = plan.response_draft
    elif not retrieval.grounded:
        spoken = (
            "माफ़ कीजिए, मेरे पास यह जानकारी नहीं है। मैं आपको मानव एजेंट से जोड़ सकता हूँ।"
            if result.language == "hi" else
            "Sorry, I don't have that information. I can connect you with a human agent."
        )
        result.handoff = True
    else:
        spoken = "कृपया दोबारा कहें।" if result.language == "hi" else "Please say that again."
    result.spoken_chunks = make_chunks(spoken)
    result.caption = spoken
    return _finalize(result, state, t0, db)


def _extract_entities_from_speech(text: str, state: ConversationState) -> None:
    """Best-effort deterministic entity capture from caller words."""
    import re
    m = re.search(r"([+]?\d[\d\s-]{8,}\d)", text)
    if m:
        digits = re.sub(r"\D", "", m.group(1))
        if len(digits) >= 10:
            state.phone_number = digits
    for name in ("मेहता", "पटेल", "शाह", "राव", "Mehta", "Patel", "Shah", "Rao", "મેહતા", "પટેલ"):
        if name.lower() in text.lower():
            state.selected_doctor = name


def _finalize(result: TurnResult, state: ConversationState, t0: float, db: Session) -> TurnResult:
    result.timings["turn_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    state.current_stage = "speaking"
    # Persist the agent turn and supporting records.
    from ..db.models import Retrieval as RetrievalRow
    from ..db.models import ToolCall, Turn

    turn = Turn(call_id=state.call_id, idx=state.turn_index, speaker="agent",
                text=result.caption, language=result.language,
                t_retrieval=result.timings.get("retrieval_ms"),
                t_plan=result.timings.get("plan_ms"),
                t_tool=result.timings.get("tool_ms"),
                t_turn_complete=result.timings.get("turn_ms"))
    db.add(turn)
    db.flush()
    if result.retrieval:
        db.add(RetrievalRow(
            turn_id=turn.id,
            chunk_ids=json.dumps([c["id"] for c in result.retrieval.get("chunks", [])]),
            scores=json.dumps([c.get("confidence", 0) for c in result.retrieval.get("chunks", [])]),
            confidence=result.retrieval.get("confidence", 0),
            execution_time_ms=result.retrieval.get("execution_time_ms", 0),
        ))
    for tool in result.tool_results:
        db.add(ToolCall(turn_id=turn.id, name=tool["name"],
                        args_json=json.dumps(tool["args"], ensure_ascii=False),
                        result_json=json.dumps(tool["data"], ensure_ascii=False),
                        execution_time_ms=result.timings.get("tool_ms", 0)))
    db.commit()
    log.info("turn_completed", extra={"call_id": state.call_id, "turn_idx": state.turn_index,
                                       "intent": state.current_intent,
                                       "duration_ms": result.timings.get("turn_ms")})
    return result
