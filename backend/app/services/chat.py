"""The RAG pipeline: question -> retrieve passages -> grounded answer + sources."""
from dataclasses import dataclass

from app.config import settings
from app.models import Hit
from app.services.llm import NOT_FOUND_MESSAGE

NO_DOCUMENTS_MESSAGE = "No documents have been uploaded yet. Upload a PDF first, then ask me about it."
SNIPPET_LENGTH = 300


@dataclass
class ChatResult:
    answer: str
    sources: list[dict]


def answer_question(question: str, history: list[dict], store, llm) -> ChatResult:
    """Answer a question using only the uploaded documents.

    1. Follow-ups are rewritten into standalone questions so retrieval works.
    2. Only passages that are close enough to the question are kept.
    3. The LLM is told to answer from those passages or admit it cannot.
    """
    if store.count() == 0:
        return ChatResult(NO_DOCUMENTS_MESSAGE, [])

    history = history[-settings.max_history_messages:]
    search_query = llm.rewrite_question(question, history) if history else question
    hits = store.search(search_query, settings.top_k, settings.max_distance)

    answer = llm.answer(question, hits, history)

    if not hits or NOT_FOUND_MESSAGE in answer:
        return ChatResult(answer, [])  # nothing was used, so nothing to cite
    return ChatResult(answer, _to_sources(hits))


def _to_sources(hits: list[Hit]) -> list[dict]:
    """One source per (document, page); hits are already sorted best-first."""
    sources: dict[tuple[str, int], dict] = {}
    for hit in hits:
        key = (hit.source, hit.page)
        if key not in sources:
            snippet = hit.text if len(hit.text) <= SNIPPET_LENGTH else hit.text[:SNIPPET_LENGTH].rstrip() + "…"
            sources[key] = {
                "document": hit.source,
                "page": hit.page,
                "snippet": snippet,
                "score": round(max(0.0, 1 - hit.distance), 2),
            }
    return list(sources.values())
