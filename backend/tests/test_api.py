"""REST API contract tests (issues #7, #8, #9)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_health_reports_storage_mode(client):
    body = client.get("/api/health").json()
    assert "storage" in body
    assert ("ephemeral" in body["storage"]) or ("SQLite file" in body["storage"])


def test_missing_call_detail_is_404(client):
    assert client.get("/api/calls/does-not-exist").status_code == 404


def test_analyze_missing_call_is_404(client):
    r = client.post("/api/calls/does-not-exist/analyze")
    assert r.status_code == 404
    assert r.json()["detail"] == "call not found"


def test_unknown_api_route_is_json_404(client):
    r = client.get("/api/this-route-does-not-exist")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/json")
    assert r.json()["detail"] == "Not Found"


def test_analyze_call_without_recordings_is_422(client):
    created = client.post("/api/calls", json={"language": "hi"}).json()
    r = client.post(f"/api/calls/{created['id']}/analyze")
    assert r.status_code == 422
    assert "no recordings" in r.json()["detail"]
