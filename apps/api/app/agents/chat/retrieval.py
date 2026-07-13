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


class CuratedOfficialRetriever:
    """Small reviewed evidence set used until the OpenSearch index is populated."""

    _evidence = (
        RetrievedEvidence(
            content=(
                "PMEGP is a credit-linked programme aimed at generating self-employment "
                "through new micro-enterprises in the non-farm sector."
            ),
            citation=Citation(
                citation_id="msme-pmegp-overview",
                document_id="pmegp",
                source_label="Ministry of MSME · PMEGP",
                source_url="https://www.msme.gov.in/offerings/schemes-and-services/details/prime-minister-employment-generation-programme-and-other-credit-support-schemes-1-MDMzETMtQWa",
                page=1,
                section="Programme description",
                excerpt="Credit-linked support for new micro-enterprises in the non-farm sector.",
            ),
        ),
        RetrievedEvidence(
            content=(
                "Udyam Registration is the official Government of India portal for MSME "
                "registration and states that registration is free and paperless."
            ),
            citation=Citation(
                citation_id="msme-udyam-registration",
                document_id="udyam",
                source_label="Ministry of MSME · Udyam Registration",
                source_url="https://www.udyamregistration.gov.in/default.aspx",
                page=1,
                section="Registration",
                excerpt="Official free and paperless MSME registration portal.",
            ),
        ),
        RetrievedEvidence(
            content=(
                "CGTMSE provides guarantee support to eligible member lending institutions "
                "for credit facilities extended to micro and small enterprises."
            ),
            citation=Citation(
                citation_id="msme-cgtmse-overview",
                document_id="cgtmse",
                source_label="CGTMSE",
                source_url="https://www.cgtmse.in/",
                page=1,
                section="Scheme overview",
                excerpt="Credit guarantee support through eligible lending institutions.",
            ),
        ),
    )

    async def retrieve(self, query: str) -> tuple[RetrievedEvidence, ...]:
        terms = {term.casefold() for term in query.split() if len(term) > 2}
        ranked = sorted(
            self._evidence,
            key=lambda item: len(terms.intersection(item.content.casefold().split())),
            reverse=True,
        )
        return tuple(ranked[:3])
