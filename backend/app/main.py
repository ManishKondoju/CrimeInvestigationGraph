# backend/app/main.py - FastAPI entrypoint for the CrimeGraphRAG API.
#
# Local dev, from the repo root:
#   venv/bin/uvicorn app.main:app --reload --app-dir backend --port 8000
#
# Production (Render): see render.yaml. Required env vars are NEO4J_URI /
# NEO4J_USER / NEO4J_PASSWORD, GROQ_API_KEY, API_KEY and ALLOWED_ORIGINS.

import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, dashboard, geo, graph_algorithms, health, network, schema, timeline
from app.security import auth_enabled, require_api_key

app = FastAPI(title="CrimeGraphRAG API", version="1.0.0")

# Comma-separated list of allowed browser origins. Defaults to the local
# Next.js dev server; production must set ALLOWED_ORIGINS to the deployed
# frontend origin(s). Never widened to "*" - credentials are allowed, and
# the two together are both unsafe and rejected by browsers.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# /health stays open so platform health checks and uptime pings work without
# holding the secret. Every data route sits behind the API key.
app.include_router(health.router)

protected = [chat, network, schema, graph_algorithms, dashboard, geo, timeline]
for module in protected:
    app.include_router(module.router, dependencies=[Depends(require_api_key)])


@app.get("/")
def root():
    """Cheap liveness/identity probe - deliberately leaks nothing sensitive."""
    return {
        "service": "CrimeGraphRAG API",
        "version": app.version,
        "auth": "enabled" if auth_enabled() else "disabled",
        "docs": "/docs",
    }
