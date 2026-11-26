"""Application settings, loaded from environment variables or backend/.env."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # LLM (Groq)
    groq_api_key: str = ""
    llm_model: str = "openai/gpt-oss-120b"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 2048

    # Embeddings (local sentence-transformers, downloaded once on first use)
    embedding_model: str = "intfloat/multilingual-e5-small"
    # e5 models expect these prefixes. For models that don't (e.g. BAAI/bge-small-en-v1.5) set both to "".
    embedding_query_prefix: str = "query: "
    embedding_document_prefix: str = "passage: "

    # Vector database (ChromaDB, stored on disk)
    chroma_dir: Path = BASE_DIR / "data" / "chroma"
    collection_name: str = "documents"

    # RAG
    chunk_size: int = 1000        # max characters per chunk
    chunk_overlap: int = 150      # characters shared between neighbouring chunks
    top_k: int = 4                # passages sent to the LLM
    max_distance: float = 1.0     # cosine distance (0-2); only a loose pre-filter, the LLM decides if the context answers

    # Limits
    max_upload_mb: int = 10
    max_history_messages: int = 10

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
