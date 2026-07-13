"""Provider-neutral generation contract and deterministic test adapter."""

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.agents.chat.state import RetrievedEvidence


class LLMGenerationRequest(BaseModel):
    """Bounded generation input independent of provider SDK types."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_message: str = Field(min_length=1, max_length=4_000)
    evidence: tuple[RetrievedEvidence, ...] = Field(min_length=1, max_length=5)
    prompt_version: str = Field(min_length=1, max_length=128)


class LLMGenerationResponse(BaseModel):
    """Validated generation response."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str = Field(min_length=1, max_length=8_000)


class LLMProvider(Protocol):
    """Application-owned interface implemented by model provider adapters."""

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        """Generate grounded text from bounded evidence."""
        ...


class DeterministicMockProvider:
    """Predictable provider for local development and tests; performs no network calls."""

    def __init__(self) -> None:
        self.calls: list[LLMGenerationRequest] = []

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        self.calls.append(request)
        citation_id = request.evidence[0].citation.citation_id
        return LLMGenerationResponse(
            text=(
                "This is a synthetic demonstration response. The retrieved demo evidence "
                f"is attached as citation {citation_id}; verify real scheme information "
                "against an approved official source."
            )
        )

