"""Validated state shared by the minimal chat graph nodes."""

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
    evidence: tuple[RetrievedEvidence, ...] = ()
    answer: str | None = Field(default=None, max_length=8_000)

