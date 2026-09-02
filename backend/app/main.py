# backend/app/main.py - FastAPI entrypoint for the CrimeGraphRAG API.
#
# Run from the repo root:
#   backend/venv/bin/uvicorn app.main:app --reload --app-dir backend --port 8000
# or, equivalently, with the repo root's venv (same deps installed there):
#   venv/bin/uvicorn app.main:app --reload --app-dir backend --port 8000

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, dashboard, geo, graph_algorithms, health, network, schema, timeline

app = FastAPI(title="CrimeGraphRAG API", version="0.1.0")

# Local dev only: Next.js runs on :3000, this API on :8000.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(network.router)
app.include_router(schema.router)
app.include_router(graph_algorithms.router)
app.include_router(dashboard.router)
app.include_router(geo.router)
app.include_router(timeline.router)
