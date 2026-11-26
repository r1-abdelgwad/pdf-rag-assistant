"""Plain data objects passed between services."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    page: int
    text: str


@dataclass(frozen=True)
class Hit:
    """A passage returned by the vector search."""
    source: str      # PDF file name
    page: int
    text: str
    distance: float  # cosine distance: 0 = identical, larger = less similar
