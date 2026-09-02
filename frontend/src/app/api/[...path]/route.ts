import { NextRequest } from "next/server";

// Server-side proxy to the FastAPI backend.
//
// The browser calls same-origin /api/*, this handler forwards to the real
// API and attaches the shared secret. That keeps API_KEY server-side only -
// putting it in a NEXT_PUBLIC_* var would ship it to every visitor and
// defeat the point of having a key at all.
//
// It also means the browser never needs cross-origin access to the backend,
// so the deployment doesn't depend on browser CORS at all.

// Read per-request rather than at module scope. Module-scope reads are
// evaluated once per cold start against whatever environment that instance
// booted with, which makes "I set the var but it still says unset" hard to
// reason about. Reading here means the values always reflect the current
// runtime environment.
// The deployed API's URL is public information, not a secret, so it ships
// as the default rather than being something every deployment must be told.
// BACKEND_URL still overrides it (needed to point a deployment at a
// different API), and local dev falls back to localhost.
const DEFAULT_BACKEND_URL =
  process.env.NODE_ENV === "development"
    ? "http://localhost:8000"
    : "https://crimegraphrag-api.onrender.com";

function readConfig() {
  const configured = process.env.BACKEND_URL;
  return {
    backendUrl: configured ?? DEFAULT_BACKEND_URL,
    apiKey: process.env.API_KEY,
    backendUrlConfigured: !!configured,
  };
}

// Force dynamic: this route must never be statically evaluated, or the
// environment would be captured at build time instead of request time.
export const dynamic = "force-dynamic";

// Streamed/download responses (CSV + schema exports) must keep their
// headers; these are the ones worth passing back through.
const PASSTHROUGH_RESPONSE_HEADERS = ["content-type", "content-disposition", "cache-control"];

async function proxy(req: NextRequest, path: string[]) {
  const { backendUrl, apiKey, backendUrlConfigured } = readConfig();
  const search = req.nextUrl.search;
  const target = `${backendUrl}/api/${path.join("/")}${search}`;

  const headers = new Headers();
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  if (apiKey) headers.set("X-API-Key", apiKey);

  let res: Response;
  try {
    res = await fetch(target, {
      method: req.method,
      headers,
      body: req.method === "GET" || req.method === "HEAD" ? undefined : await req.text(),
      // The LangGraph agent can take a while (entity extraction, Cypher
      // generation, retries, answer synthesis), so don't let a default
      // cache or revalidation policy interfere.
      cache: "no-store",
    });
  } catch (e) {
    // Backend unreachable: cold start on Render's free tier, backend down,
    // or - most commonly on a fresh deploy - BACKEND_URL simply not set.
    // Report the origin we actually tried (never the API key) so the cause
    // is obvious from the response alone.
    const origin = new URL(backendUrl).origin;
    const hint = !backendUrlConfigured
      ? " (BACKEND_URL is not set, so this fell back to localhost - set it in the deployment environment and redeploy)"
      : "";
    return Response.json(
      {
        detail: `Upstream API unreachable at ${origin}: ${(e as Error).message}${hint}`,
        backend: origin,
        backend_url_configured: backendUrlConfigured,
        api_key_configured: !!apiKey,
      },
      { status: 502 },
    );
  }

  const outHeaders = new Headers();
  for (const h of PASSTHROUGH_RESPONSE_HEADERS) {
    const v = res.headers.get(h);
    if (v) outHeaders.set(h, v);
  }

  return new Response(res.body, { status: res.status, headers: outHeaders });
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function POST(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
