"""HTTP and SSE contracts for chat."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.agents.chat.state import Citation


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=4_000)


class StatusEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event: Literal["status"] = "status"
    status: Literal["retrieving", "generating"]


class CitationPreviewEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event: Literal["citation_preview"] = "citation_preview"
    citation: Citation


class TextDeltaEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event: Literal["text_delta"] = "text_delta"
    text: str = Field(min_length=1, max_length=500)


class FinalEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event: Literal["final"] = "final"
    message_id: UUID
    citations: tuple[Citation, ...]
    prompt_version: str


type ChatStreamEvent = StatusEvent | CitationPreviewEvent | TextDeltaEvent | FinalEvent


def encode_sse(event: ChatStreamEvent) -> str:
    """Serialize a typed event using the SSE event/data framing contract."""
    return f"event: {event.event}\ndata: {event.model_dump_json()}\n\n"

