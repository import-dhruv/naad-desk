"""Compatibility re-export for the findings seed data.

Single source of truth: ``backend/app/findings_data.py``. The backend service
imports it directly (Vercel service root is ``backend/``); recon scripts use
this shim so both paths stay in sync.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.findings_data import FINDINGS, seed_findings  # noqa: E402,F401

__all__ = ["FINDINGS", "seed_findings"]
