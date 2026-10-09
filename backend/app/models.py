from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, max_length=120)
    # Últimos mensajes de la conversación; los envía el widget para que el asistente tenga memoria.
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    grounded: bool


class SourceRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=200_000)
    source_url: str | None = Field(default=None, max_length=1000)


class UrlSourceRequest(BaseModel):
    url: str = Field(min_length=8, max_length=1000)


class HealthResponse(BaseModel):
    status: str
    supabase_connected: bool
    gemini_configured: bool
