"""Async Oogam REST client: Sutra chat, TTS, batch STT.

The API key is only ever used here (server-side). Every response is logged to
the `api_calls` table with status, latency, non-sensitive headers and cost.
Authoritative cost is read from X-Naad-Cost-Paise when present; otherwise a
labelled estimate from published rates is used.
"""
from __future__ import annotations

import json
import time
from typing import Any

import httpx

from ..config import settings
from ..db.database import SessionLocal
from ..db.models import ApiCall
from ..logging_util import log


class SpendGuard:
    """Aborts new upstream requests once the per-run ceiling is reached."""

    def __init__(self, ceiling_paise: int) -> None:
        self.ceiling = ceiling_paise
        self.spent = 0.0

    def check(self) -> None:
        if self.spent >= self.ceiling:
            raise RuntimeError("spend_ceiling_reached")

    def add(self, paise: float) -> None:
        self.spent += paise


spend_guard = SpendGuard(settings.cost_ceiling_paise)


def _naad_headers(response: httpx.Response) -> dict[str, str]:
    out = {}
    for key, value in response.headers.items():
        if key.lower().startswith("x-naad"):
            out[key] = value
    return out


def _cost_from(response: httpx.Response, fallback_paise: float) -> float:
    raw = response.headers.get("x-naad-cost-paise")
    if raw is not None:
        try:
            return float(raw)
        except ValueError:
            pass
    return fallback_paise


def _log_api(call_id: str | None, endpoint: str, status: int,
             headers: dict[str, str], latency_ms: float, cost: float) -> None:
    try:
        db = SessionLocal()
        try:
            db.add(ApiCall(call_id=call_id, endpoint=endpoint, status=status,
                           headers_json=json.dumps(headers), latency_ms=latency_ms,
                           cost_paise=cost))
            db.commit()
        finally:
            db.close()
    except Exception as exc:  # logging must never break the call
        log.warning("api_call_log_failed", extra={"error": str(exc)})


class OogamClient:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=settings.rest_base, timeout=30.0,
                headers=settings.auth_headers(),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _post(self, path: str, *, call_id: str | None = None, **kwargs) -> httpx.Response:
        spend_guard.check()
        start = time.perf_counter()
        response = await (await self._http()).post(path, **kwargs)
        latency = round((time.perf_counter() - start) * 1000, 2)
        headers = _naad_headers(response)
        _log_api(call_id, path, response.status_code, headers, latency, 0)
        if response.status_code >= 400:
            log.error("oogam_http_error", extra={
                "endpoint": path, "status": response.status_code,
                "body": response.text[:300], "latency_ms": latency, "call_id": call_id,
            })
            response.raise_for_status()
        return response

    async def chat_json(self, messages: list[dict[str, Any]], call_id: str | None = None,
                        model: str | None = None, retries: int = 1) -> dict[str, Any]:
        """Sutra chat with json_object mode. Retries once on invalid JSON."""
        payload = {
            "model": model or settings.sutra_model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        last_error = ""
        for attempt in range(retries + 1):
            try:
                response = await self._post("/chat/completions", call_id=call_id, json=payload)
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    raise ValueError("plan is not a JSON object")
                usage = data.get("usage", {})
                cost = (
                    usage.get("prompt_tokens", 0) * settings.rate_sutra_in_paise_per_1m / 1_000_000
                    + usage.get("completion_tokens", 0) * settings.rate_sutra_out_paise_per_1m / 1_000_000
                )
                spend_guard.add(cost)
                return parsed
            except Exception as exc:
                last_error = str(exc)
                log.warning("sutra_plan_parse_failed", extra={"attempt": attempt, "error": last_error})
        return {"intent": "faq", "clarification": "कृपया दोबारा कहें।", "_error": last_error}

    async def tts(self, text: str, voice: str = "aditi", language: str = "HIN",
                  call_id: str | None = None) -> bytes:
        payload = {"model": settings.tts_model, "input": text,
                   "voice": voice, "language": language}
        response = await self._post("/audio/speech", call_id=call_id, json=payload)
        cost = _cost_from(response, len(text) * settings.rate_tts_paise_per_1k_chars / 1000)
        spend_guard.add(cost)
        return response.content

    async def stt(self, audio: bytes, language: str = "HIN", verbose: bool = True,
                  call_id: str | None = None) -> dict[str, Any]:
        files = {"file": ("audio.wav", audio, "audio/wav")}
        data = {"model": settings.stt_model, "language": language,
                "response_format": "verbose_json" if verbose else "text"}
        response = await self._post("/audio/transcriptions", call_id=call_id,
                                    data=data, files=files)
        try:
            return response.json()
        except Exception:
            return {"text": response.text}


oogam = OogamClient()
