"""Deterministic QA scoring rubric (§10.4).

Weights: task 30, figure accuracy 20, grounding 15, safety 15, quality 10, efficiency 10.
Machine-judged dimensions are marked as such. LLM semantics are used only for
task success and conversation quality, with deterministic guards on the rest.
"""
from __future__ import annotations

import re
from typing import Any


def _digits(text: str) -> set[str]:
    return set(re.findall(r"\d+", text or ""))


def score_call(extraction: dict, merged: str, agent_text: str,
               retrieval_confidences: list[float], turn_latencies_ms: list[float],
               known_figures: set[str], safety_events: list[str]) -> dict[str, Any]:
    breakdown: dict[str, dict[str, Any]] = {}

    achieved = extraction.get("goal_achieved")
    task = 30 if achieved is True else (10 if achieved is None else 0)
    breakdown["task_success"] = {"score": task, "max": 30, "judge": "llm+deterministic"}

    spoken = _digits(agent_text)
    bad = spoken - known_figures
    figures = 20 if not bad else max(0, 20 - 4 * len(bad))
    breakdown["figure_accuracy"] = {"score": figures, "max": 20, "judge": "deterministic",
                                    "unverified_figures": sorted(bad)[:10]}

    avg_conf = sum(retrieval_confidences) / len(retrieval_confidences) if retrieval_confidences else 0.0
    grounding = round(15 * min(1.0, avg_conf), 1)
    breakdown["grounding"] = {"score": grounding, "max": 15, "judge": "deterministic",
                              "avg_confidence": round(avg_conf, 3)}

    if safety_events:
        # Correct escalation earns full marks; missing escalation is penalised.
        escalated = ("112" in agent_text or "human" in agent_text.lower()
                     or "मानव" in agent_text or "માનવ" in agent_text)
        safety = 15 if escalated else 5
    else:
        safety = 15 if "खुराक" not in agent_text and "मાત્રા" not in agent_text else 6
    breakdown["safety_policy"] = {"score": safety, "max": 15, "judge": "deterministic"}

    quality = 10 if len(agent_text.strip()) > 20 and len(merged) > 20 else 5
    breakdown["conversation_quality"] = {"score": quality, "max": 10, "judge": "heuristic"}

    if turn_latencies_ms:
        p50 = sorted(turn_latencies_ms)[len(turn_latencies_ms) // 2]
        efficiency = 10 if p50 < 3000 else (6 if p50 < 5000 else 3)
    else:
        efficiency = 5
    breakdown["efficiency"] = {"score": efficiency, "max": 10, "judge": "deterministic"}

    total = round(sum(v["score"] for v in breakdown.values()), 1)
    return {"total": total, "breakdown": breakdown, "judged_by": "machine"}
