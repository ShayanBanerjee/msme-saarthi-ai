"""HTTP and SSE contracts for chat."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.agents.chat.state import AdvisorMode, BusinessContext, Citation, ResponseDepth
from app.features.chat.models import MessageRole


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=4_000)
    business_context: BusinessContext = Field(default_factory=BusinessContext)
    advisor_mode: AdvisorMode = AdvisorMode.BUSINESS_ANALYST
    response_depth: ResponseDepth = ResponseDepth.BALANCED


class StatusEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event: Literal["status"] = "status"
    status: Literal["understanding", "retrieving", "generating"]


class ChatHistoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: MessageRole
    content: str
    citation_ids: tuple[str, ...]


class ChatHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    conversation_id: UUID
    items: tuple[ChatHistoryItem, ...]


class CitationPreviewEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event: Literal["citation_preview"] = "citation_preview"
    citation: Citation


class TextDeltaEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event: Literal["text_delta"] = "text_delta"
    text: str = Field(min_length=1, max_length=500)


class TextReplaceEvent(BaseModel):
    """Replace provisional deltas after timeout or failed claim validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event: Literal["text_replace"] = "text_replace"
    text: str = Field(min_length=1, max_length=8_000)


class FinalEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event: Literal["final"] = "final"
    message_id: UUID
    citations: tuple[Citation, ...]
    prompt_version: str
    completion_status: Literal["validated", "fallback"] = "validated"
    fallback_reason: Literal["provider_timeout", "citation_validation_failed"] | None = None


class ErrorEvent(BaseModel):
    """Safe terminal stream failure that never exposes provider internals."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event: Literal["error"] = "error"
    code: Literal["answer_generation_failed"] = "answer_generation_failed"
    message: str = "Saarthi could not complete this answer. Please retry."
    retryable: bool = True


type ChatStreamEvent = (
    StatusEvent
    | CitationPreviewEvent
    | TextDeltaEvent
    | TextReplaceEvent
    | FinalEvent
    | ErrorEvent
)


def encode_sse(event: ChatStreamEvent) -> str:
    """Serialize a typed event using the SSE event/data framing contract."""
    return f"event: {event.event}\ndata: {event.model_dump_json()}\n\n"
