"""Validated state shared by the minimal chat graph nodes."""

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Citation(BaseModel):
    """Resolvable synthetic citation metadata returned by retrieval."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    citation_id: str = Field(min_length=1, max_length=128)
    document_id: str = Field(min_length=1, max_length=128)
    source_label: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    page: int = Field(ge=1)
    section: str = Field(min_length=1, max_length=200)
    excerpt: str = Field(min_length=1, max_length=500)
    source_kind: Literal["official_scheme", "business_guide"] = "official_scheme"
    license_label: str | None = Field(default=None, max_length=100)


class BusinessStage(StrEnum):
    IDEA = "idea"
    STARTING = "starting"
    OPERATING = "operating"
    SCALING = "scaling"


class BusinessGoal(StrEnum):
    START = "start"
    FUND = "fund"
    SELL = "sell"
    FORMALISE = "formalise"
    IMPROVE = "improve"


class BusinessContext(BaseModel):
    """Small user-confirmed brief used to focus retrieval and advice."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: BusinessStage | None = None
    goal: BusinessGoal | None = None
    location: str | None = Field(default=None, min_length=2, max_length=80)
    sector: str | None = Field(default=None, min_length=2, max_length=120)

    def retrieval_text(self) -> str:
        values = (self.stage, self.goal, self.location, self.sector)
        return " ".join(str(value) for value in values if value is not None)


class ConversationMessage(BaseModel):
    """Bounded prior visible message; hidden reasoning is never retained."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8_000)


class RetrievedEvidence(BaseModel):
    """Untrusted retrieval content and its application-issued citation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    content: str = Field(min_length=1, max_length=2_000)
    citation: Citation


class ChatGraphState(BaseModel):
    """Minimal graph state with no credentials, hidden reasoning, or arbitrary tools."""

    model_config = ConfigDict(extra="forbid")

    conversation_id: UUID
    actor_id: UUID
    tenant_id: UUID
    correlation_id: UUID
    user_message: str = Field(min_length=1, max_length=4_000)
    prompt_version: str = Field(default="chat.synthetic.v1", min_length=1, max_length=128)
    business_context: BusinessContext = Field(default_factory=BusinessContext)
    conversation: tuple[ConversationMessage, ...] = Field(default=(), max_length=12)
    evidence: tuple[RetrievedEvidence, ...] = ()
    answer: str | None = Field(default=None, max_length=8_000)
