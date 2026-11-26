"""Chat endpoint."""
from fastapi import APIRouter, Depends

from app.schemas import ChatRequest, ChatResponse
from app.services.chat import answer_question
from app.services.llm import LLMClient, get_llm_client
from app.services.vector_store import VectorStore, get_vector_store

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    store: VectorStore = Depends(get_vector_store),
    llm: LLMClient = Depends(get_llm_client),
):
    history = [message.model_dump() for message in request.history]
    result = answer_question(request.message, history, store, llm)
    return ChatResponse(answer=result.answer, sources=result.sources)
