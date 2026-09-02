import type {
  ChatRequest,
  ChatResponse,
  EntityOption,
  EntityTypesResponse,
  NetworkGraph,
  SchemaData,
  SchemaExportFormat,
  SchemaSample,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function postChat(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new ApiError(detail || res.statusText, res.status);
  }

  return res.json();
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new ApiError(detail || res.statusText, res.status);
  }
  return res.json();
}

export function getEntityTypes(): Promise<EntityTypesResponse> {
  return getJson("/api/network/entity-types");
}

export function getEntities(type: string): Promise<EntityOption[]> {
  return getJson(`/api/network/entities?type=${encodeURIComponent(type)}`);
}

export function getNetworkGraph(type: string, id?: string | number | null): Promise<NetworkGraph> {
  const params = new URLSearchParams({ type });
  if (id != null) params.set("id", String(id));
  return getJson(`/api/network/graph?${params.toString()}`);
}

export function getSchema(): Promise<SchemaData> {
  return getJson("/api/schema");
}

export function getSchemaSample(label: string): Promise<SchemaSample> {
  return getJson(`/api/schema/sample/${encodeURIComponent(label)}`);
}

export function schemaExportUrl(fmt: SchemaExportFormat): string {
  return `${API_BASE}/api/schema/export/${fmt}`;
}
