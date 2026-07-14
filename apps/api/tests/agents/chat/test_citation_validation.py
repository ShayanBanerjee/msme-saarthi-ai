"""Synthetic claim-level citation validation tests."""

from typing import Literal

from app.agents.chat.citation_validation import (
    CitationValidationCode,
    validate_claim_citations,
)
from app.agents.chat.state import Citation, RetrievedEvidence


def _evidence(
    *,
    citation_id: str = "synthetic-credit",
    kind: Literal["official_scheme", "business_guide"] = "official_scheme",
) -> tuple[RetrievedEvidence, ...]:
    return (
        RetrievedEvidence(
            content=(
                "The Synthetic Credit Programme provides guarantee support for working-capital "
                "credit up to INR 10 lakh through participating lenders."
            ),
            citation=Citation(
                citation_id=citation_id,
                document_id="synthetic-document",
                source_label="Synthetic Credit Programme",
                source_url="https://example.invalid/synthetic-credit",
                page=1,
                section="Synthetic terms",
                excerpt="Synthetic guarantee support for credit.",
                source_kind=kind,
            ),
        ),
    )


def test_supported_same_claim_citation_passes() -> None:
    result = validate_claim_citations(
        "Synthetic Credit Programme provides guarantee support for credit up to INR 10 lakh "
        "[synthetic-credit].",
        _evidence(),
    )

    assert result.valid
    assert result.cited_ids == ("synthetic-credit",)


def test_numeric_mismatch_and_uncited_claim_fail() -> None:
    mismatched = validate_claim_citations(
        "Synthetic Credit Programme provides credit up to INR 50 lakh [synthetic-credit].",
        _evidence(),
    )
    uncited = validate_claim_citations(
        "Synthetic Credit Programme provides guarantee support for credit.", _evidence()
    )

    assert CitationValidationCode.UNSUPPORTED_CLAIM in mismatched.codes
    assert CitationValidationCode.UNCITED_MATERIAL_CLAIM in uncited.codes


def test_allowlisted_but_semantically_mismatched_citation_fails() -> None:
    result = validate_claim_citations(
        "A founder should redesign the workshop logo [synthetic-credit].", _evidence()
    )

    assert CitationValidationCode.UNSUPPORTED_CLAIM in result.codes


def test_unknown_non_official_and_eligibility_claims_fail() -> None:
    unknown = validate_claim_citations(
        "Synthetic Credit Programme provides credit [unknown-source].", _evidence()
    )
    guide = validate_claim_citations(
        "Synthetic Credit Programme provides credit [synthetic-guide].",
        _evidence(citation_id="synthetic-guide", kind="business_guide"),
    )
    eligibility = validate_claim_citations(
        "You are eligible for Synthetic Credit Programme [synthetic-credit].", _evidence()
    )

    assert CitationValidationCode.UNKNOWN_CITATION in unknown.codes
    assert CitationValidationCode.NON_OFFICIAL_SCHEME_SOURCE in guide.codes
    assert CitationValidationCode.ELIGIBILITY_ASSERTION in eligibility.codes
