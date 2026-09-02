# Smoke test hitting every endpoint once against a live Neo4j instance.
# Run from backend/: ../venv/bin/pytest tests/ -v

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["neo4j"] == "up"


def test_chat():
    r = client.post("/api/chat", json={"question": "Give me database statistics", "conversation_history": []})
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"answer", "sources", "cypher_queries", "context"}


def test_network_entity_types():
    r = client.get("/api/network/entity-types")
    assert r.status_code == 200
    assert "Person" in r.json()["types"]


def test_network_entities_and_graph():
    r = client.get("/api/network/entities", params={"type": "Person"})
    assert r.status_code == 200
    entities = r.json()
    assert len(entities) > 0

    r2 = client.get("/api/network/graph", params={"type": "Person", "id": entities[0]["id"]})
    assert r2.status_code == 200
    assert "nodes" in r2.json() and "edges" in r2.json()


def test_schema():
    r = client.get("/api/schema")
    assert r.status_code == 200
    assert len(r.json()["nodes"]) > 0


def test_schema_sample_rejects_unknown_label():
    r = client.get("/api/schema/sample/NotARealLabel")
    assert r.status_code == 400


@pytest.mark.parametrize(
    "path",
    [
        "/api/graph/pagerank",
        "/api/graph/communities",
        "/api/graph/degree-centrality",
        "/api/graph/betweenness-centrality",
        "/api/graph/persons",
        "/api/graph/stats",
    ],
)
def test_graph_algorithm_endpoints(path):
    r = client.get(path)
    assert r.status_code == 200


@pytest.mark.parametrize(
    "path",
    [
        "/api/dashboard/kpis",
        "/api/dashboard/trends",
        "/api/dashboard/gangs",
        "/api/dashboard/breakdowns",
        "/api/dashboard/operations",
        "/api/dashboard/activity",
    ],
)
def test_dashboard_endpoints(path):
    r = client.get(path)
    assert r.status_code == 200


def test_geo_locations_and_injection():
    r = client.get("/api/geo/locations", params={"limit": 100})
    assert r.status_code == 200
    assert r.json()["count"] > 0

    # malicious-looking filter value must be treated as a literal, not executed
    r2 = client.get("/api/geo/locations", params={"crime_types": "' OR 1=1 --"})
    assert r2.status_code == 200
    assert r2.json()["count"] == 0


def test_timeline_data_and_injection():
    r = client.get("/api/timeline/data", params={"severity": "critical"})
    assert r.status_code == 200
    rows = r.json()["rows"]
    assert len(rows) > 0
    assert all(row["severity"] == "critical" for row in rows)

    r2 = client.get("/api/timeline/data", params={"crime_types": "' OR 1=1 --"})
    assert r2.status_code == 200
    assert r2.json()["count"] == 0
