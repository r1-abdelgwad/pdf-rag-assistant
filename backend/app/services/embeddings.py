"""Local embeddings via sentence-transformers (no API key required).

The model is downloaded from the Hugging Face Hub on the first call and cached
locally by the sentence-transformers library.  Subsequent calls are instant.
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import settings

BATCH_SIZE = 32


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load the model once and reuse it for the lifetime of the process."""
    return SentenceTransformer(settings.embedding_model)


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Vectors for document chunks (passage-prefixed, normalised), in the same order."""
    prefixed = [settings.embedding_document_prefix + t for t in texts]
    model = _get_model()
    vectors: list[list[float]] = []
    for start in range(0, len(prefixed), BATCH_SIZE):
        batch = prefixed[start : start + BATCH_SIZE]
        embeddings = model.encode(batch, normalize_embeddings=True)
        vectors.extend(e.tolist() for e in embeddings)
    return vectors


def embed_query(text: str) -> list[float]:
    """Vector for a user question (query-prefixed, normalised)."""
    prefixed = settings.embedding_query_prefix + text
    model = _get_model()
    embedding = model.encode(prefixed, normalize_embeddings=True)
    return embedding.tolist()
