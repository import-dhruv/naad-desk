"""Automated 24-scenario replay runner (PRD §19.3).

Each scenario drives the real gateway WebSocket with typed caller utterances
(text_input), captures the agent's real replies and tool calls, and evaluates
explicit assertions. Results are written from observed events only — an
untested or failed scenario is never reported as passed.

Run with the backend on 127.0.0.1:8100:
    .venv/bin/python scripts/run_scenarios.py
"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from websockets.asyncio.client import connect

ROOT = Path(__file__).resolve().parents[1]
WS = "ws://127.0.0.1:8100/ws/call"

SCENARIOS = [
    dict(id="S01", name="Clinic timings", turns=["क्लिनिक का समय क्या है?"], expect=["सोमवार", "शनिवार"], db="none"),
    dict(id="S02", name="Consultation fee", turns=["डॉक्टर मेहता की फी कितनी है?"], expect=["500"], db="none"),
    dict(id="S03", name="Next available appointment", turns=["अगली उपलब्ध अपॉइंटमेंट बुक करनी है"], expect=["उपलब्ध", "समय"], db="none"),
    dict(id="S04", name="Specific doctor/date/time", turns=["डॉक्टर पटेल के लिए कल सुबह 10 बजे अपॉइंटमेंट चाहिए"], expect=["Patel", "15:00"], db="none"),
    dict(id="S05", name="Relative date", turns=["कल सुबह अपॉइंटमेंट चाहिए"], expect=["समय"], db="none"),
    dict(id="S06", name="Unavailable slot", turns=["रविवार को अपॉइंटमेंट चाहिए"], expect=["उपलब्ध"], db="none"),
    dict(id="S07", name="Reschedule", turns=["मेरी अपॉइंटमेंट बदलनी है, फोन 9876500001"], expect=["पुष्टि"], db="none"),
    dict(id="S08", name="Cancel", turns=["मेरी अपॉइंटमेंट रद्द करनी है, फोन 9876500001"], expect=["रद्द"], db="none"),
    dict(id="S09", name="Documents required", turns=["अपॉइंटमेंट के लिए कौन से दस्तावेज़ लाने हैं?"], expect=["प्रिस्क्रिप्शन"], db="none"),
    dict(id="S10", name="Location and parking", turns=["क्लिनिक कहाँ है और पार्किंग है?"], expect=[], db="none"),
    dict(id="S11", name="Medicine request", turns=["बुखार के लिए दवा दीजिए"], expect=["डॉक्टर"], db="none"),
    dict(id="S12", name="Emergency", turns=["छाती में दर्द हो रहा है"], expect=["112"], db="none"),
    dict(id="S13", name="Human handoff", turns=["मुझे मानव एजेंट से बात करनी है"], expect=[], db="none"),
    dict(id="S14", name="Interrupt long response", turns=["डॉक्टर मेहता के बारे में विस्तार से बताइए"], expect=[], db="none"),
    dict(id="S15", name="Hindi to English switch", turns=["अंग्रेज़ी में बात करते हैं। What are the clinic hours?"], expect=["9"], db="none"),
    dict(id="S16", name="Gujarati to Hindi switch", turns=["હિંદીમાં બોલો। ક્લિનિકનો સમય શું છે?"], expect=["શનિવાર"], db="none"),
    dict(id="S17", name="Extended silence", turns=["..."], expect=[], db="none"),
    dict(id="S18", name="Background noise", turns=["शोर है, क्या आप सुन रहे हैं?"], expect=[], db="none"),
    dict(id="S19", name="Spell unusual name", turns=["मेरा नाम सी-एच-ए-आर है"], expect=[], db="none"),
    dict(id="S20", name="Dictate phone", turns=["मेरा फोन नंबर 98765 43210 है"], expect=[], db="none"),
    dict(id="S21", name="Unrelated question", turns=["आज शेयर बाजार कैसा है?"], expect=[], db="none"),
    dict(id="S22", name="Ambiguous date", turns=["शुक्रवार को अपॉइंटमेंट चाहिए"], expect=[], db="none"),
    dict(id="S23", name="Fee then booking", turns=["फी कितनी है? फिर अपॉइंटमेंट बुक करते हैं"], expect=["500"], db="none"),
    dict(id="S24", name="Correct a date", turns=["कल बुक किया, नहीं शनिवार को कर दीजिए"], expect=[], db="none"),
]


async def run_scenario(sc: dict) -> dict:
    captions: list[str] = []
    tools: list[str] = []
    errors: list[str] = []
    start = time.perf_counter()
    try:
        async with connect(WS, open_timeout=10) as ws:
            await ws.send(json.dumps({"v": 1, "type": "start", "language": "hi", "disclosure_ack": True}))
            # Wait for session.ready
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if msg["type"] == "session.ready":
                    break
            for utterance in sc["turns"]:
                before = len(captions)
                await ws.send(json.dumps({"v": 1, "type": "text_input", "text": utterance}))
                # Wait for an agent caption after this utterance.
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline and len(captions) == before:
                    try:
                        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=20))
                    except asyncio.TimeoutError:
                        break
                    if msg["type"] == "caption" and msg["payload"].get("speaker") == "agent":
                        captions.append(msg["payload"].get("text", ""))
                    if msg["type"] == "tool":
                        tools.extend(t.get("name", "") for t in msg["payload"].get("calls", []))
                    if msg["type"] == "error":
                        errors.append(msg["payload"].get("detail", ""))
            await ws.send(json.dumps({"v": 1, "type": "end", "reason": "scenario"}))
            try:
                while True:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
                    if msg["type"] in ("tool", "caption"):
                        if msg["type"] == "tool":
                            tools.extend(t.get("name", "") for t in msg["payload"].get("calls", []))
                        elif msg["payload"].get("speaker") == "agent":
                            captions.append(msg["payload"].get("text", ""))
                    if msg["type"] == "call.ended":
                        break
            except asyncio.TimeoutError:
                pass
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    blob = " ".join(captions)
    matched = {exp: (exp.lower() in blob.lower()) for exp in sc["expect"]}
    # A scenario passes when every explicit expectation is observed and no
    # upstream/gateway error occurred. Scenarios with no explicit expectation
    # are marked "observed" (evidence captured, assertion not specified).
    if errors:
        status = "fail"
    elif sc["expect"]:
        status = "pass" if all(matched.values()) else "fail"
    else:
        status = "observed"
    return {
        "id": sc["id"], "name": sc["name"], "status": status,
        "input": sc["turns"], "expected": sc["expect"], "matched": matched,
        "agent_replies": captions, "tools": tools, "errors": errors,
        "duration_seconds": round(time.perf_counter() - start, 2),
        "db_state": sc["db"], "evidence": "gateway WebSocket events",
    }


async def main() -> None:
    results = []
    for sc in SCENARIOS:
        result = await run_scenario(sc)
        results.append(result)
        print(f"{result['id']}: {result['status']:8} {result['name']:32} tools={result['tools']}")
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transport": "text_input replay over WS /ws/call (live backend + Oogam)",
        "total": len(results),
        "passed": sum(r["status"] == "pass" for r in results),
        "observed": sum(r["status"] == "observed" for r in results),
        "failed": sum(r["status"] == "fail" for r in results),
        "results": results,
    }
    out = ROOT / "recon" / "results" / "scenarios.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# 24-Scenario Replay Results", "",
          f"Generated: {report['generated_at']}", "",
          f"Passed {report['passed']} · Observed {report['observed']} · Failed {report['failed']} · Total {report['total']}", "",
          "| ID | Scenario | Status | Tools |", "|---|---|---|---|"]
    for r in results:
        md.append(f"| {r['id']} | {r['name']} | {r['status']} | {', '.join(r['tools']) or '—'} |")
    (ROOT / "recon" / "results" / "scenarios.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n", report["passed"], "passed,", report["observed"], "observed,", report["failed"], "failed")


if __name__ == "__main__":
    asyncio.run(main())
