"""Environment-driven configuration.

No secrets are hardcoded. Loads `.env` from the project root when present.
All values have safe development defaults so the app can boot without a `.env`,
but upstream calls require a real OOGAM_API_KEY.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV"))

# Locally the backend lives in <repo>/backend/app/. On Vercel the backend is its
# own service root, so config.py is <service>/app/config.py.
ROOT = Path(__file__).resolve().parents[1] if IS_VERCEL else Path(__file__).resolve().parents[2]


def _load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _default_db_url() -> str:
    # Vercel Functions have a read-only filesystem except /tmp.
    if IS_VERCEL:
        return "sqlite:////tmp/naad_desk.db"
    return "sqlite:///./naad_desk.db"


def _get_int(name: str, default: int) -> int:
    try:
        return int(_get(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    oogam_api_key: str = field(default_factory=lambda: _get("OOGAM_API_KEY", ""))
    rest_base: str = field(default_factory=lambda: _get("OOGAM_REST_BASE", "https://platform.oogam.ai/v1"))
    ws_url: str = field(default_factory=lambda: _get("OOGAM_WS_URL", "wss://platform.oogam.ai/v1/realtime?v=2"))
    sutra_model: str = field(default_factory=lambda: _get("OOGAM_SUTRA_MODEL", "sutra-conversation"))
    tts_model: str = field(default_factory=lambda: _get("OOGAM_TTS_MODEL", "naad-tts-v2"))
    stt_model: str = field(default_factory=lambda: _get("OOGAM_STT_MODEL", "naad-stt-v2"))

    voice: str = field(default_factory=lambda: _get("NAAD_VOICE", "f1"))
    lang: str = field(default_factory=lambda: _get("NAAD_LANG", "hi"))
    vad_end_silence_ms: int = field(default_factory=lambda: _get_int("VAD_END_SILENCE_MS", 700))

    app_env: str = field(default_factory=lambda: _get("APP_ENV", "development"))
    host: str = field(default_factory=lambda: _get("APP_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _get_int("APP_PORT", 8000))
    database_url: str = field(default_factory=lambda: _get("DATABASE_URL", _default_db_url()))
    is_vercel: bool = IS_VERCEL
    log_level: str = field(default_factory=lambda: _get("LOG_LEVEL", "INFO"))

    cost_ceiling_paise: int = field(default_factory=lambda: _get_int("COST_CEILING_PAISE", 5000))
    monthly_budget_paise: int = field(default_factory=lambda: _get_int("MONTHLY_BUDGET_PAISE", 100000))
    max_call_seconds: int = field(default_factory=lambda: _get_int("MAX_CALL_SECONDS", 600))
    reconnect_backoff_ms: tuple[int, ...] = field(
        default_factory=lambda: tuple(
            int(x) for x in _get("RECONNECT_BACKOFF_MS", "1000,2000,4000").split(",") if x.strip()
        )
    )

    embedding_model: str = field(default_factory=lambda: _get("EMBEDDING_MODEL", "intfloat/multilingual-e5-small"))
    retrieval_top_k: int = field(default_factory=lambda: _get_int("RETRIEVAL_TOP_K", 4))
    retrieval_min_confidence: float = field(default_factory=lambda: float(_get("RETRIEVAL_MIN_CONFIDENCE", "0.50")))
    timezone: str = field(default_factory=lambda: _get("TZ", "Asia/Kolkata"))

    # Published rates (paise) for *estimates* only — authoritative cost comes from
    # X-Naad-Cost-Paise headers when present. See decisions.md D-12.
    rate_sts_paise_per_min: int = 38
    rate_tts_paise_per_1k_chars: int = 150
    rate_sutra_in_paise_per_1m: int = 1500
    rate_sutra_out_paise_per_1m: int = 6000

    @property
    def has_api_key(self) -> bool:
        return bool(self.oogam_api_key) and not self.oogam_api_key.startswith("sk-setu-REPLACE")

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.oogam_api_key}"}


settings = Settings()
