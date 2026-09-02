# Tests for the shared-secret API gate.
#
# These matter more than they look: every data endpoint hits Neo4j and
# /api/chat spends Groq tokens per call, so if this gate silently stops
# enforcing, a public deployment leaks both data and money. The rest of the
# suite runs with API_KEY unset (gate disabled), so without these tests a
# regression here would go unnoticed.

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

KEY = "unit-test-key"
PROTECTED = "/api/dashboard/kpis"


@pytest.fixture
def auth_on(monkeypatch):
    monkeypatch.setenv("API_KEY", KEY)


@pytest.fixture
def auth_off(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)


def test_rejects_missing_key(auth_on):
    assert client.get(PROTECTED).status_code == 401


def test_rejects_wrong_key(auth_on):
    assert client.get(PROTECTED, headers={"X-API-Key": "nope"}).status_code == 401


def test_rejects_key_prefix(auth_on):
    """A truncated key must fail - guards against prefix/length comparison."""
    assert client.get(PROTECTED, headers={"X-API-Key": KEY[:-1]}).status_code == 401


def test_accepts_correct_key(auth_on):
    assert client.get(PROTECTED, headers={"X-API-Key": KEY}).status_code == 200


def test_health_stays_open(auth_on):
    """Platform health checks and uptime pings must not need the secret."""
    assert client.get("/health").status_code == 200


def test_root_reports_auth_enabled(auth_on):
    assert client.get("/").json()["auth"] == "enabled"


def test_open_when_unconfigured(auth_off):
    """No API_KEY set -> gate disabled, so local dev stays frictionless."""
    assert client.get(PROTECTED).status_code == 200
    assert client.get("/").json()["auth"] == "disabled"
