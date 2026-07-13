"""Validated query, filter, OpenSearch response, and result models."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class SchemeStatus(StrEnum):
    PUBLISHED = "published"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class LanguageCode(StrEnum):
    ENGLISH = "en"
    HINDI = "hi"


class SourceKind(StrEnum):
    OFFICIAL_SCHEME = "official_scheme"
    BUSINESS_GUIDE = "business_guide"


class RetrievalFilters(BaseModel):
    """Allowlisted structured filters; unknown values fail validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    state: str | None = Field(default=None, min_length=2, max_length=3, pattern=r"^[A-Z]{2,3}$")
    scheme_status: SchemeStatus = SchemeStatus.PUBLISHED
    language: LanguageCode | None = None
    effective_on: date | None = None
    source_kind: SourceKind | None = None

    @field_validator("state", mode="before")
    @classmethod
    def normalize_state(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value


class RetrievalQuery(BaseModel):
    """Typed hybrid search request constructed by application code."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    query: str = Field(min_length=1, max_length=500)
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
    limit: int = Field(default=10, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def normalized_query(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("query must contain non-whitespace characters")
        return normalized


class OpenSearchDocument(BaseModel):
    """Strict index document contract for published retrieval chunks."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    chunk_id: str = Field(min_length=1, max_length=128)
    chunk_text: str = Field(min_length=1, max_length=20_000)
    citation_id: str = Field(min_length=1, max_length=128)
    document_id: str = Field(min_length=1, max_length=128)
    source_label: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    page: int = Field(ge=1)
    section: str = Field(min_length=1, max_length=300)
    state_codes: tuple[str, ...] = ()
    scheme_status: SchemeStatus
    language: LanguageCode
    valid_from: date
    valid_until: date | None = None
    source_kind: SourceKind = SourceKind.OFFICIAL_SCHEME
    license_label: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def valid_effective_period(self) -> "OpenSearchDocument":
        if self.valid_until is not None and self.valid_until < self.valid_from:
            raise ValueError("valid_until must not precede valid_from")
        return self


class OpenSearchHit(BaseModel):
    """Validated subset of one OpenSearch hit."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    hit_id: str = Field(alias="_id", min_length=1)
    score: float = Field(alias="_score", ge=0)
    source: OpenSearchDocument = Field(alias="_source")


class OpenSearchHits(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    hits: tuple[OpenSearchHit, ...]


class OpenSearchResponse(BaseModel):
    """Validated external OpenSearch response boundary."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    hits: OpenSearchHits


class RetrievalResult(BaseModel):
    """Fused result with source/citation metadata preserved."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_chunk_id: str
    content: str
    rrf_score: float = Field(gt=0)
    lexical_rank: int | None = Field(default=None, ge=1)
    vector_rank: int | None = Field(default=None, ge=1)
    citation_id: str
    document_id: str
    source_label: str
    source_url: HttpUrl
    page: int = Field(ge=1)
    section: str
    scheme_status: SchemeStatus
    language: LanguageCode
    valid_from: date
    valid_until: date | None
    source_kind: SourceKind
    license_label: str | None
