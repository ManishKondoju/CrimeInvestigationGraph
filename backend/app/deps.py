# backend/app/deps.py - shared singleton providers for FastAPI routes.
#
# The Neo4j Database wrapper and the LangGraph agent already exist at the
# repo root (database.py, langgraph_agent.py) and are reused here as-is -
# nothing is duplicated. Make sure the repo root is importable regardless
# of how uvicorn was invoked (`uvicorn backend.app.main:app` from the repo
# root does NOT always put the root on sys.path, depending on the shell/
# entrypoint used), then import from there.

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from database import Database  # noqa: E402
from langgraph_agent import CrimeInvestigationAgent  # noqa: E402
from network_viz import NetworkVisualization  # noqa: E402
from schema_visualizer import SchemaVisualizer  # noqa: E402
from graph_algorithms import GraphAlgorithms  # noqa: E402
from geo_mapping import CrimeGeographicMapper  # noqa: E402

_db: Database | None = None
_agent: CrimeInvestigationAgent | None = None
_network_viz: NetworkVisualization | None = None
_schema_viz: SchemaVisualizer | None = None
_graph_algorithms: GraphAlgorithms | None = None
_geo_mapper: CrimeGeographicMapper | None = None


def get_db() -> Database:
    """FastAPI dependency: shared Database (Neo4j driver) singleton."""
    global _db
    if _db is None:
        _db = Database()
    return _db


def get_agent() -> CrimeInvestigationAgent:
    """FastAPI dependency: shared LangGraph agent singleton."""
    global _agent
    if _agent is None:
        _agent = CrimeInvestigationAgent()
    return _agent


def get_network_viz() -> NetworkVisualization:
    """FastAPI dependency: shared NetworkVisualization (query logic only -
    its .render()/._render_d3_network() Streamlit methods are never called
    here, only get_all_entities_of_type()/get_network_data())."""
    global _network_viz
    if _network_viz is None:
        _network_viz = NetworkVisualization(get_db())
    return _network_viz


def get_schema_viz() -> SchemaVisualizer:
    """FastAPI dependency: shared SchemaVisualizer (data methods only)."""
    global _schema_viz
    if _schema_viz is None:
        _schema_viz = SchemaVisualizer(get_db())
    return _schema_viz


def get_graph_algorithms() -> GraphAlgorithms:
    """FastAPI dependency: shared GraphAlgorithms singleton."""
    global _graph_algorithms
    if _graph_algorithms is None:
        _graph_algorithms = GraphAlgorithms(get_db())
    return _graph_algorithms


def get_geo_mapper() -> CrimeGeographicMapper:
    """FastAPI dependency: shared CrimeGeographicMapper - only its pure
    predict_hotspots() method is used here; get_crime_locations() is NOT
    reused (it's the injection-vulnerable version - see geo_service.py)."""
    global _geo_mapper
    if _geo_mapper is None:
        _geo_mapper = CrimeGeographicMapper(get_db())
    return _geo_mapper
