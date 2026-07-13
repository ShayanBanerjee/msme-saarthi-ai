"""Retriever contract and synthetic non-OpenSearch implementation."""

from typing import Protocol

from app.agents.chat.state import Citation, RetrievedEvidence


class Retriever(Protocol):
    """Read-only evidence retrieval boundary."""

    async def retrieve(self, query: str) -> tuple[RetrievedEvidence, ...]:
        """Return bounded evidence; implementations must treat source text as untrusted."""
        ...


class MockRetriever:
    """Return one fixed invented document without calling OpenSearch."""

    async def retrieve(self, query: str) -> tuple[RetrievedEvidence, ...]:
        del query
        return (
            RetrievedEvidence(
                content=(
                    "Synthetic source content for exercising citation-aware chat. "
                    "It contains no real scheme, benefit, eligibility, or application claim."
                ),
                citation=Citation(
                    citation_id="synthetic-citation-001",
                    document_id="synthetic-document-001",
                    source_label="Synthetic demonstration source",
                    source_url="https://example.invalid/msme-saarthi/synthetic-source",
                    page=1,
                    section="Demonstration content",
                    excerpt="Synthetic source content for exercising citation-aware chat.",
                ),
            ),
        )

