import type {
  ChatRequest,
  DashboardActivity,
  DashboardBreakdowns,
  DashboardKpis,
  DashboardOperations,
  DashboardTrends,
  GangIntel,
  ChatResponse,
  CrimeLocation,
  EntityOption,
  EntityTypesResponse,
  GeoFilters,
  HotspotPrediction,
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

function geoParams(filters: GeoFilters): URLSearchParams {
  const params = new URLSearchParams();
  filters.crime_types?.forEach((t) => params.append("crime_types", t));
  filters.districts?.forEach((d) => params.append("districts", d));
  if (filters.start_date) params.set("start_date", filters.start_date);
  if (filters.end_date) params.set("end_date", filters.end_date);
  if (filters.limit) params.set("limit", String(filters.limit));
  return params;
}

export function getCrimeTypes(): Promise<{ types: string[] }> {
  return getJson("/api/geo/crime-types");
}

export function getDistricts(): Promise<{ districts: string[] }> {
  return getJson("/api/geo/districts");
}

export function getCrimeLocations(filters: GeoFilters): Promise<{ count: number; rows: CrimeLocation[] }> {
  return getJson(`/api/geo/locations?${geoParams(filters).toString()}`);
}

export function getHotspots(filters: GeoFilters): Promise<{ count: number; predictions: HotspotPrediction[] }> {
  return getJson(`/api/geo/hotspots?${geoParams(filters).toString()}`);
}

export function geoExportCsvUrl(filters: GeoFilters): string {
  return `${API_BASE}/api/geo/export.csv?${geoParams(filters).toString()}`;
}

export function getKpis(): Promise<DashboardKpis> {
  return getJson("/api/dashboard/kpis");
}

export function getTrends(): Promise<DashboardTrends> {
  return getJson("/api/dashboard/trends");
}

export function getGangs(): Promise<{ gangs: GangIntel[] }> {
  return getJson("/api/dashboard/gangs");
}

export function getBreakdowns(): Promise<DashboardBreakdowns> {
  return getJson("/api/dashboard/breakdowns");
}

export function getOperations(): Promise<DashboardOperations> {
  return getJson("/api/dashboard/operations");
}

export function getActivity(): Promise<DashboardActivity> {
  return getJson("/api/dashboard/activity");
}
