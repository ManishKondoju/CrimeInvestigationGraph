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
