"""End-to-end gateway test: browser-style WebSocket -> backend -> Oogam.

Exercises the complete chain: session start, upstream handshake, greeting,
a grounded FAQ turn (Sutra + hybrid retrieval + say + binary audio), and end.
"""
from __future__ import annotations

import asyncio
import json
import os

from websockets.asyncio.client import connect


async def main() -> None:
    url = os.getenv("NAAD_GATEWAY_WS", "ws://127.0.0.1:8100/ws/call")
    async with connect(url, open_timeout=10) as ws:
        await ws.send(json.dumps({"v": 1, "type": "start", "language": "hi",
                                  "disclosure_ack": True}))
        seen: dict[str, int] = {}
        captions: list[str] = []
        audio_frames = 0
        done = False

        async def sender() -> None:
            await asyncio.sleep(2.0)
            await ws.send(json.dumps({"v": 1, "type": "text_input",
                                      "text": "डॉक्टर मेहता की कन्सल्टेशन फी कितनी है?"}))
            await asyncio.sleep(12.0)
            await ws.send(json.dumps({"v": 1, "type": "end", "reason": "test"}))

        task = asyncio.create_task(sender())
        try:
            while not done:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=25)
                except asyncio.TimeoutError:
                    break
                msg = json.loads(raw)
                t = msg.get("type")
                seen[t] = seen.get(t, 0) + 1
                if t == "audio":
                    audio_frames += 1
                if t == "caption":
                    captions.append(msg["payload"].get("text", ""))
                if t == "call.ended":
                    done = True
        finally:
            task.cancel()
        print("EVENTS:", seen)
        print("AUDIO FRAMES:", audio_frames)
        print("CAPTIONS:")
        for c in captions:
            print("  -", c[:180])


if __name__ == "__main__":
    asyncio.run(main())
