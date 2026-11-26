"""Request and response models of the HTTP API."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(max_length=2000)
    history: list[Message] = []

    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty.")
        return value


class Source(BaseModel):
    document: str
    page: int
    snippet: str
    score: float  # similarity between 0 and 1, higher is better


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


class DocumentInfo(BaseModel):
    filename: str
    pages: int
    chunks: int
