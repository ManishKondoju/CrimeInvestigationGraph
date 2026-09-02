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

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const API_KEY = process.env.API_KEY;
// Only meaningful in local dev - in any real deployment an unset BACKEND_URL
// means every request dies at localhost, so surface that in the error below
// rather than emitting a bare "fetch failed".
const BACKEND_URL_IS_DEFAULT = !process.env.BACKEND_URL;

// Streamed/download responses (CSV + schema exports) must keep their
// headers; these are the ones worth passing back through.
const PASSTHROUGH_RESPONSE_HEADERS = ["content-type", "content-disposition", "cache-control"];

async function proxy(req: NextRequest, path: string[]) {
  const search = req.nextUrl.search;
  const target = `${BACKEND_URL}/api/${path.join("/")}${search}`;

  const headers = new Headers();
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  if (API_KEY) headers.set("X-API-Key", API_KEY);

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
    const origin = new URL(BACKEND_URL).origin;
    const hint = BACKEND_URL_IS_DEFAULT
      ? " (BACKEND_URL is not set, so this fell back to localhost - set it in the deployment environment and redeploy)"
      : "";
    return Response.json(
      {
        detail: `Upstream API unreachable at ${origin}: ${(e as Error).message}${hint}`,
        backend: origin,
        backend_url_configured: !BACKEND_URL_IS_DEFAULT,
        api_key_configured: !!API_KEY,
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
