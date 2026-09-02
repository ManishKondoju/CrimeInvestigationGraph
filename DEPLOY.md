# Deploying CrimeGraphRAG

Three pieces:

| Piece | Runs on | Notes |
|---|---|---|
| Neo4j (data) | **Neo4j Aura** | already provisioned |
| FastAPI (`backend/`) | **Render** | web service, builds from repo root |
| Next.js (`frontend/`) | **Vercel** | also proxies API calls server-side |

The browser never talks to the API directly. It calls the Next.js app's
`/api/*` route handler, which forwards to Render and attaches the shared
secret. That keeps `API_KEY` off the client and means the deployment does
not depend on browser CORS.

```
browser ──► Vercel (Next.js)  ──X-API-Key──►  Render (FastAPI)  ──►  Neo4j Aura
```

---

## 1. Backend → Render

The service **builds from the repo root, not `backend/`** — the API reuses
root-level modules (`database.py`, `langgraph_agent.py`, `network_viz.py`,
`graph_algorithms.py`, `schema_visualizer.py`, `geo_mapping.py`,
`timeline_viz.py`) instead of duplicating their query logic.

1. Render Dashboard → **New → Blueprint** → point at this repo. It reads
   [`render.yaml`](render.yaml).
2. Set the secrets Render prompts for (all marked `sync: false`):

   | Variable | Value |
   |---|---|
   | `NEO4J_URI` | `neo4j+s://<instance>.databases.neo4j.io` |
   | `NEO4J_USER` | Aura username |
   | `NEO4J_PASSWORD` | Aura password |
   | `GROQ_API_KEY` | from console.groq.com |
   | `ALLOWED_ORIGINS` | Vercel URL, e.g. `https://<app>.vercel.app` |

   `API_KEY` is generated automatically by Render (`generateValue: true`) —
   copy it, you need it for Vercel in step 2.

3. Verify:
   ```bash
   curl https://<service>.onrender.com/health          # {"status":"ok","neo4j":"up"}
   curl https://<service>.onrender.com/                 # "auth":"enabled"
   curl https://<service>.onrender.com/api/dashboard/kpis   # 401 -> gate is live
   ```
   If `auth` reports `disabled`, `API_KEY` didn't get set — fix before
   going public.

## 2. Frontend → Vercel

1. Vercel → **Add New → Project** → import the repo, set **Root Directory
   to `frontend`**.
2. Environment variables (Production + Preview). Neither is
   `NEXT_PUBLIC_` — that prefix would inline them into the browser bundle:

   | Variable | Value |
   |---|---|
   | `BACKEND_URL` | `https://<service>.onrender.com` |
   | `API_KEY` | the value Render generated |

3. Deploy, then set Render's `ALLOWED_ORIGINS` to the real Vercel URL and
   redeploy the backend.

## 3. Post-deploy checks

```bash
curl https://<app>.vercel.app/api/dashboard/kpis   # 200 via the proxy
```
Then in the browser: load `/dashboard`, run a `/chat` query, expand the
Cypher trace, and switch all three `/geo` modes.

---

## Things that will bite you

**Neo4j Aura free tier pauses after ~3 days idle.** The app returns
`neo4j: down` until you resume it from the Aura console. For anything
long-lived, use a paid instance or ping it on a schedule.

**Render free tier spins down when idle** — the first request after a
quiet period takes ~50s while the service wakes. The proxy surfaces this
as a `502 Upstream API unreachable` rather than hanging forever. Upgrade
the plan, or accept the cold start.

**Groq spend is only as protected as `API_KEY`.** The gate stops casual
abuse, but anyone holding the key can run unlimited LLM queries. If the
key leaks, rotate it in both Render and Vercel. There is currently **no
rate limiting** — worth adding if this stays public.

**Never set `NEXT_PUBLIC_API_BASE_URL` in production.** It exists as a
local debugging escape hatch that bypasses the proxy; setting it in prod
would point browsers straight at the backend, which then needs real CORS
and still wouldn't have the key.

**The backend image includes Streamlit and Plotly.** Not used by the API,
but the reused page modules import them at module top. Removing them means
extracting the query logic into pure-Python services first.

## Local development

```bash
# backend (repo root)
venv/bin/uvicorn app.main:app --reload --app-dir backend --port 8000

# frontend
cd frontend && npm run dev
```

With no `API_KEY` set the gate is disabled, so local dev needs no secret.
To rehearse production wiring, set `API_KEY` in both the backend
environment and `frontend/.env.local`.
