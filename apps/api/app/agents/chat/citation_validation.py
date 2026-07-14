"""Deterministic claim-level citation checks for untrusted model output."""

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.agents.chat.state import RetrievedEvidence

_CITATION_PATTERN = re.compile(r"\[([A-Za-z0-9._:-]+)\]")
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_CLAIM_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n+")
_MATERIAL_TERMS = {
    "apply",
    "application",
    "benefit",
    "collateral",
    "credit",
    "deadline",
    "finance",
    "grant",
    "guarantee",
    "interest",
    "loan",
    "programme",
    "registration",
    "scheme",
    "subsidy",
    "support",
}
_STOP_WORDS = {
    "and",
    "are",
    "for",
    "from",
    "government",
    "india",
    "official",
    "programme",
    "scheme",
    "source",
    "support",
    "that",
    "the",
    "this",
    "with",
}
_ELIGIBILITY_ASSERTION = re.compile(
    r"\b(?:you|your business|your enterprise)\s+(?:are|is|will be|qualif(?:y|ies))\s+"
    r"(?:eligible|qualified)|\byou\s+(?:can|will)\s+(?:get|receive)\b",
    re.IGNORECASE,
)
_NON_CLAIM = re.compile(
    r"\b(?:no|insufficient|outdated)\b.*\bevidence\b|\bnot an? eligibility\b|"
    r"\bevidence leads?\b",
    re.IGNORECASE,
)


class CitationValidationCode(StrEnum):
    UNKNOWN_CITATION = "unknown_citation"
    UNCITED_MATERIAL_CLAIM = "uncited_material_claim"
    NON_OFFICIAL_SCHEME_SOURCE = "non_official_scheme_source"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    ELIGIBILITY_ASSERTION = "eligibility_assertion"


class CitationValidationResult(BaseModel):
    """Machine-readable result suitable for metrics without retaining model text."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    valid: bool
    codes: tuple[CitationValidationCode, ...] = ()
    cited_ids: tuple[str, ...] = ()


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in _TOKEN_PATTERN.findall(value.casefold())
        if len(token) > 2 and token not in _STOP_WORDS
    }


def _is_material_claim(claim: str, evidence: tuple[RetrievedEvidence, ...]) -> bool:
    if _NON_CLAIM.search(claim):
        return False
    lowered = claim.casefold()
    if any(term in _tokens(claim) for term in _MATERIAL_TERMS):
        return True
    if re.search(r"(?:₹|\b(?:rs\.?|inr)\b|\d+(?:\.\d+)?\s*%)", lowered):
        return True
    return any(
        len(_tokens(item.citation.source_label).intersection(_tokens(claim))) >= 2
        for item in evidence
        if item.citation.source_kind == "official_scheme"
    )


def validate_claim_citations(
    answer: str, evidence: tuple[RetrievedEvidence, ...]
) -> CitationValidationResult:
    """Require same-claim, official, lexically and numerically supporting citations."""
    by_id = {item.citation.citation_id: item for item in evidence}
    codes: list[CitationValidationCode] = []
    cited_ids: list[str] = []
    for claim in (part.strip(" -\t") for part in _CLAIM_BOUNDARY.split(answer)):
        if not claim:
            continue
        claim_citations = _CITATION_PATTERN.findall(claim)
        cited_ids.extend(claim_citations)
        if any(citation_id not in by_id for citation_id in claim_citations):
            codes.append(CitationValidationCode.UNKNOWN_CITATION)
        if _ELIGIBILITY_ASSERTION.search(claim):
            codes.append(CitationValidationCode.ELIGIBILITY_ASSERTION)
        material_claim = _is_material_claim(claim, evidence)
        if material_claim and not claim_citations:
            codes.append(CitationValidationCode.UNCITED_MATERIAL_CLAIM)
            continue
        if not claim_citations:
            continue
        claim_without_markers = _CITATION_PATTERN.sub("", claim)
        claim_tokens = _tokens(claim_without_markers)
        claim_numbers = set(re.findall(r"\d+(?:\.\d+)?", claim_without_markers))
        supported = False
        citation_problem = False
        for citation_id in claim_citations:
            item = by_id.get(citation_id)
            if item is None:
                citation_problem = True
                continue
            if material_claim and item.citation.source_kind != "official_scheme":
                codes.append(CitationValidationCode.NON_OFFICIAL_SCHEME_SOURCE)
                citation_problem = True
                continue
            support_text = f"{item.citation.source_label} {item.content}"
            support_tokens = _tokens(support_text)
            support_numbers = set(re.findall(r"\d+(?:\.\d+)?", support_text))
            meaningful_overlap = len(claim_tokens.intersection(support_tokens)) >= 2
            numbers_match = not claim_numbers or claim_numbers.issubset(support_numbers)
            if meaningful_overlap and numbers_match:
                supported = True
        if not supported and not citation_problem:
            codes.append(CitationValidationCode.UNSUPPORTED_CLAIM)
    unique_codes = tuple(dict.fromkeys(codes))
    return CitationValidationResult(
        valid=not unique_codes,
        codes=unique_codes,
        cited_ids=tuple(dict.fromkeys(cited_ids)),
    )
