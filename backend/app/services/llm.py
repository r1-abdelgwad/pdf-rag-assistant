"""LLM access (Groq) and the prompts used by the RAG pipeline."""
import logging
from functools import lru_cache

import groq
from groq import Groq

from app.config import settings
from app.errors import AppError
from app.models import Hit

logger = logging.getLogger(__name__)

NOT_FOUND_MESSAGE = "I couldn't find this information in the uploaded documents."

ANSWER_PROMPT = """You are an assistant that answers questions strictly from the user's uploaded PDF documents.

Rules:
1. Use ONLY the information in the CONTEXT below. Never use outside knowledge and never guess.
2. If the CONTEXT does not contain the answer, reply with exactly this sentence and nothing else: "{not_found}"
3. If the user only greets you or says thanks, reply briefly and invite them to ask about their documents.
4. Use the conversation history only to understand follow-up questions. Facts must come from the CONTEXT.
5. Answer in the same language as the user's question. Be concise. Use plain text (simple "-" lists are fine, no markdown formatting).

CONTEXT:
{context}"""

REWRITE_PROMPT = (
    "Rewrite the user's last message as a standalone question, using the conversation to resolve "
    "references such as 'it', 'that policy' or 'and the second one?'. Keep the language of the message. "
    "Return ONLY the rewritten question. If it is already standalone, or is not a question, return it unchanged."
)


class LLMError(AppError):
    """The LLM call failed."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message, status_code)


class LLMClient:
    def __init__(self, api_key: str) -> None:
        self._client = Groq(api_key=api_key)

    def rewrite_question(self, question: str, history: list[dict]) -> str:
        """Turn a follow-up ("and what about the second one?") into a standalone search query."""
        transcript = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content'][:500]}" for m in history
        )
        rewritten = self._complete(
            [
                {"role": "system", "content": REWRITE_PROMPT},
                {"role": "user", "content": f"Conversation:\n{transcript}\n\nLast message: {question}"},
            ],
            temperature=0,
            max_tokens=400,
        )
        return rewritten or question

    def answer(self, question: str, hits: list[Hit], history: list[dict]) -> str:
        context = (
            "\n\n".join(f"[{i}] {h.source}, page {h.page}\n{h.text}" for i, h in enumerate(hits, start=1))
            if hits
            else "(no relevant passages found)"
        )
        system = ANSWER_PROMPT.format(not_found=NOT_FOUND_MESSAGE, context=context)
        messages = [{"role": "system", "content": system}, *history, {"role": "user", "content": question}]
        return self._complete(
            messages, temperature=settings.llm_temperature, max_tokens=settings.llm_max_tokens
        )

    def _complete(self, messages: list[dict], *, temperature: float, max_tokens: int) -> str:
        try:
            response = self._client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **_extra_options(),
            )
        except groq.AuthenticationError as exc:
            raise LLMError("The Groq API key is invalid. Check GROQ_API_KEY in backend/.env.", 503) from exc
        except groq.RateLimitError as exc:
            raise LLMError("The LLM rate limit was reached. Please try again in a moment.", 429) from exc
        except groq.APIConnectionError as exc:
            raise LLMError("Could not reach the LLM service. Check your internet connection.", 502) from exc
        except groq.APIStatusError as exc:
            logger.error("Groq API error: %s", exc)
            raise LLMError(f"The LLM service returned an error ({exc.status_code}): {exc.message}", 502) from exc
        return (response.choices[0].message.content or "").strip()


def _extra_options() -> dict:
    """gpt-oss models think before answering; keep that short so answers stay fast."""
    if settings.llm_model.startswith("openai/gpt-oss"):
        return {"extra_body": {"reasoning_effort": "low"}}
    return {}


@lru_cache
def get_llm_client() -> LLMClient:
    if not settings.groq_api_key:
        raise LLMError("GROQ_API_KEY is not set. Add it to backend/.env and restart the server.", 503)
    return LLMClient(settings.groq_api_key)
