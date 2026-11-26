"""Vector database (ChromaDB) wrapper. Vectors come from services/embeddings.py (Hugging Face)."""
import logging
import re
from functools import lru_cache

import chromadb

from app.config import settings
from app.models import Chunk, Hit
from app.services.embeddings import embed_documents, embed_query

BATCH_SIZE = 100
logger = logging.getLogger(__name__)



class VectorStore:
    def __init__(self) -> None:
        client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        # One collection per embedding model, so vectors from different models are never mixed.
        model_slug = re.sub(r"[^a-zA-Z0-9]+", "_", settings.embedding_model).strip("_")
        self._collection = client.get_or_create_collection(
            name=f"{settings.collection_name}_{model_slug}"[:63].rstrip("_"),
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return self._collection.count()

    def add_document(self, filename: str, chunks: list[Chunk]) -> None:
        """Store a document's chunks. Re-uploading the same file replaces it."""
        self.delete_document(filename)
        for start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[start:start + BATCH_SIZE]
            self._collection.add(
                ids=[f"{filename}::{start + i}" for i in range(len(batch))],
                documents=[c.text for c in batch],
                embeddings=embed_documents([c.text for c in batch]),
                metadatas=[{"source": filename, "page": c.page} for c in batch],
            )

    def search(self, query: str, k: int, max_distance: float) -> list[Hit]:
        """Return up to k passages closest to the query, dropping irrelevant ones."""
        total = self.count()
        if total == 0:
            return []
        result = self._collection.query(
            query_embeddings=[embed_query(query)],
            n_results=min(k, total),
            include=["documents", "metadatas", "distances"],
        )
        hits = [
            Hit(source=meta["source"], page=meta["page"], text=text, distance=distance)
            for text, meta, distance in zip(
                result["documents"][0], result["metadatas"][0], result["distances"][0]
            )
        ]
        logger.info("Search %r -> distances %s (max allowed %s)", query, [round(h.distance, 2) for h in hits], max_distance)
        return [hit for hit in hits if hit.distance <= max_distance]

    def list_documents(self) -> list[dict]:
        metadatas = self._collection.get(include=["metadatas"])["metadatas"] or []
        documents: dict[str, dict] = {}
        for meta in metadatas:
            doc = documents.setdefault(meta["source"], {"pages": set(), "chunks": 0})
            doc["pages"].add(meta["page"])
            doc["chunks"] += 1
        return [
            {"filename": name, "pages": len(info["pages"]), "chunks": info["chunks"]}
            for name, info in sorted(documents.items())
        ]

    def delete_document(self, filename: str) -> bool:
        """Remove a document. Returns False if it was not stored."""
        existing = self._collection.get(where={"source": filename}, limit=1)
        if not existing["ids"]:
            return False
        self._collection.delete(where={"source": filename})
        return True


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore()
