"""Embeddings from the Hugging Face Inference API (hf-inference provider)."""
import httpx

from app.config import settings
from app.errors import AppError

BATCH_SIZE = 32
URL = "https://router.huggingface.co/hf-inference/models/{model}/pipeline/feature-extraction"


class EmbeddingError(AppError):
    pass


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Vectors for document chunks, in the same order."""
    prefixed = [settings.embedding_document_prefix + t for t in texts]
    vectors: list[list[float]] = []
    for start in range(0, len(prefixed), BATCH_SIZE):
        vectors.extend(_embed_batch(prefixed[start:start + BATCH_SIZE]))
    return vectors


def embed_query(text: str) -> list[float]:
    """Vector for a user question."""
    return _embed_batch([settings.embedding_query_prefix + text])[0]


def _embed_batch(texts: list[str]) -> list[list[float]]:
    if not settings.hf_token:
        raise EmbeddingError("HF_TOKEN is not set. Add it to backend/.env and restart the server.", 503)

    try:
        response = httpx.post(
            URL.format(model=settings.embedding_model),
            headers={"Authorization": f"Bearer {settings.hf_token}"},
            json={"inputs": texts},
            timeout=120,
        )
    except httpx.HTTPError as exc:
        raise EmbeddingError("Could not reach Hugging Face. Check your internet connection.", 502) from exc

    status = response.status_code
    if status in (401, 403):
        raise EmbeddingError("The Hugging Face token is invalid or lacks the 'Inference Providers' permission.", 503)
    if status == 404:
        raise EmbeddingError(f"Model '{settings.embedding_model}' is not available on Hugging Face Inference.", 503)
    if status == 429:
        raise EmbeddingError("Hugging Face rate limit reached. Please try again in a moment.", 429)
    if status == 503:
        raise EmbeddingError("The embedding model is loading on Hugging Face. Try again in a moment.", 503)
    if status != 200:
        raise EmbeddingError(f"Hugging Face returned an error ({status}): {response.text[:200]}", 502)

    return [_pool(vector) for vector in response.json()]


def _pool(vector: list) -> list[float]:
    """Some models return one vector per token; average them into one vector per text."""
    if vector and isinstance(vector[0], list):
        return [sum(column) / len(vector) for column in zip(*vector)]
    return vector
