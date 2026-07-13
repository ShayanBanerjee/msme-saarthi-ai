"""Chat domain models."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Persistable message without hidden model reasoning."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    actor_id: UUID
    tenant_id: UUID
    role: MessageRole
    content: str = Field(min_length=1, max_length=8_000)
    citation_ids: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuthenticatedActor(BaseModel):
    """Trusted actor context supplied by the future authentication module."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    actor_id: UUID
    tenant_id: UUID

