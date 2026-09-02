from typing import Any

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    conversation_history: list[ChatMessage] = []
    thread_id: str | None = None


class CypherQuery(BaseModel):
    name: str
    cypher: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    cypher_queries: list[CypherQuery]
    context: dict[str, Any]
