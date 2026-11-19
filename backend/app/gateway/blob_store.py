"""Durable recordings on Vercel Blob.

Local/Docker deployments keep WAV files on disk. On Vercel each function has a
separate /tmp, so recordings are uploaded to the connected private Blob store and
their URLs are recorded in calls.metadata_json.
"""
from __future__ import annotations

import json
import os
from typing import Any

from ..config import settings
from ..logging_util import log

_BLOB_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN", "")
_BLOB_STORE_ID = os.getenv("BLOB_STORE_ID", "")


def _session():
    """Build an SDK session with explicit static credentials (works on Vercel)."""
    from vercel import blob
    from vercel.api import session
    from vercel.blob import BlobCredentials

    def factory() -> BlobCredentials:
        return BlobCredentials(token=_BLOB_TOKEN, store_id=_BLOB_STORE_ID)

    return session(service_options=[blob.BlobServiceOptions(credentials_factory=factory)])


async def upload_recording(call_id: str, channel: str, data: bytes) -> str | None:
    if not settings.is_vercel or not (_BLOB_TOKEN and _BLOB_STORE_ID):
        return None
    try:
        from vercel import blob
        async with _session():
            result = await blob.put_blob(
                f"recordings/{call_id}/{channel}.wav", data,
                access="private", content_type="audio/wav", allow_overwrite=True,
            )
            return str(result.url)
    except Exception as exc:
        log.warning("blob_upload_failed", extra={"call_id": call_id, "channel": channel,
                                                   "error": str(exc)})
        return None


async def download_recording(reference: str) -> bytes | None:
    if not (_BLOB_TOKEN and _BLOB_STORE_ID):
        return None
    try:
        from vercel import blob
        async with _session():
            result = await blob.get_blob(reference, access="private")
            return bytes(result.body)
    except Exception as exc:
        log.warning("blob_download_failed", extra={"error": str(exc)})
        return None


def recording_refs(call_metadata: str | None) -> dict[str, str]:
    if not call_metadata:
        return {}
    try:
        data: Any = json.loads(call_metadata)
        refs = data.get("recording_refs", {}) if isinstance(data, dict) else {}
        return refs if isinstance(refs, dict) else {}
    except (ValueError, TypeError):
        return {}
