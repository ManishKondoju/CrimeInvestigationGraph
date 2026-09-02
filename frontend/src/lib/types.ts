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

// Mirrors backend/app/routers/dashboard.py -> app/services/dashboard_service.py.
// Six aggregate endpoints replacing enhanced_dashboard.py's ~30 inline queries.

export interface DashboardKpis {
  total_crimes: number;
  open_cases: number;
  critical_crimes: number;
  solve_rate: number;
  districts: string[];
  total_persons: number;
  total_organizations: number;
  total_evidence: number;
  total_weapons: number;
  insights: {
    high_risk_suspects: number;
    active_gangs: number;
    critical_evidence: number;
    weapons_recovered: number;
    repeat_offenders: { total: number; max_crimes: number };
    armed_gang_members: { total: number; gangs: number; weapons: number };
    network_hubs: { total: number; max_connections: number };
  };
}

export interface MonthlyTrend {
  year_month: string;
  total_crimes: number;
  severe_crimes: number;
  solved_crimes: number;
}

export interface DashboardTrends {
  monthly_trends: MonthlyTrend[];
  pipeline: { total: number; open: number; investigating: number; solved: number; cold: number };
}

export interface GangIntel {
  gang: string;
  territory: string | null;
  type: string | null;
  members: number;
  crimes: number;
  weapons: number;
  severe_crimes: number;
  threat_level: number;
}

export interface DashboardBreakdowns {
  crime_types: { type: string; count: number }[];
  severity: { severity: string; count: number }[];
  districts: { district: string; crimes: number }[];
  weapon_status: { type: string; total: number; recovered: number; at_large: number }[];
  evidence_significance: { significance: string; total: number; verified: number }[];
}

export interface DashboardOperations {
  investigators: {
    investigator: string;
    department: string | null;
    total_cases: number;
    solved: number;
    active: number;
    solve_rate: number;
  }[];
  district_heatmap: { district: string; total: number; severe: number; other: number }[];
  hotspots: { location: string; district: string | null; crimes: number; severe: number }[];
}

export interface DashboardActivity {
  recent_incidents: {
    id: string;
    type: string;
    date: string;
    time: string | null;
    severity: string;
    status: string;
    location: string;
    district: string;
    suspect: string | null;
  }[];
  peak_hour: string | null;
  priority_targets: {
    name: string;
    age: number;
    crimes: number;
    weapons: number;
    gang: string;
    priority: string;
  }[];
  data_quality: {
    orphaned_crimes: number;
    no_evidence_crimes: number;
    unsolved_severe: number;
    independent_suspects: number;
  };
}
