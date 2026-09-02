// Mirrors backend/app/models/chat.py's Pydantic models exactly.

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  question: string;
  conversation_history: ChatMessage[];
  thread_id?: string | null;
}

export interface CypherQuery {
  name: string;
  cypher: string;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  cypher_queries: CypherQuery[];
  context: Record<string, unknown>;
}

// A rendered chat turn - ChatMessage plus the transparency-panel data that
// only assistant turns carry (mirrors app.py's chat_history entries).
export interface ChatTurn extends ChatMessage {
  cypher_queries?: CypherQuery[];
  context?: Record<string, unknown>;
}

// Mirrors backend/app/models/network.py and backend/app/routers/network.py.

export const NETWORK_ENTITY_TYPES = [
  "Organization",
  "Person",
  "Crime",
  "Location",
  "Investigator",
  "Evidence",
  "Weapon",
  "Vehicle",
] as const;

export type NetworkEntityType = (typeof NETWORK_ENTITY_TYPES)[number];

export interface EntityTypesResponse {
  types: NetworkEntityType[];
  colors: Record<string, string>;
}

export interface EntityOption {
  id: string | number;
  name: string;
}

export interface NetworkNode {
  id: string | number;
  label: string | null;
  type: string;
}

export interface NetworkEdge {
  source: string | number;
  target: string | number;
  label: string;
}

export interface NetworkGraph {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

// Mirrors backend/app/models/schema_models.py and backend/app/routers/schema.py.

export interface SchemaNodeType {
  node_type: string;
  count: number;
}

export interface SchemaRelationshipType {
  source_type: string;
  relationship_type: string;
  target_type: string;
  count: number;
}

export interface SchemaData {
  nodes: SchemaNodeType[];
  relationships: SchemaRelationshipType[];
  properties: Record<string, string[]>;
}

export interface SchemaSample {
  label: string;
  samples: Record<string, unknown>[];
}

export type SchemaExportFormat = "json" | "cypher" | "markdown";

// Mirrors backend/app/routers/geo.py and backend/app/services/geo_service.py.

export interface CrimeLocation {
  case_id: string;
  crime_type: string;
  date: string;
  severity: string;
  status: string;
  arrest_made: boolean;
  latitude: number;
  longitude: number;
  location_name: string;
  district: string;
}

export interface HotspotPrediction {
  latitude: number;
  longitude: number;
  crime_count: number;
  severe_count: number;
  risk_score: number;
  risk_level: string;
  primary_crime: string;
  district: string;
  arrest_rate: number;
}

export interface GeoFilters {
  crime_types?: string[];
  start_date?: string;
  end_date?: string;
  districts?: string[];
  limit?: number;
}
