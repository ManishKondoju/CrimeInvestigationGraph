from fastapi import APIRouter, Depends

from app.deps import get_agent
from app.models.chat import ChatRequest, ChatResponse, CypherQuery

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, agent=Depends(get_agent)):
    history = [m.model_dump() for m in req.conversation_history]

    result = agent.ask_with_context(req.question, history, thread_id=req.thread_id)

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        cypher_queries=[CypherQuery(name=name, cypher=cypher) for name, cypher in result["cypher_queries"]],
        context=result["context"],
    )
