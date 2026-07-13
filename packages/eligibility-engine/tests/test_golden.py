"""Golden behavior tests using invented schemes and profiles only."""

import json
from pathlib import Path
from typing import Any

import pytest

from eligibility_engine import BusinessProfile, SchemeRuleSet, evaluate

GOLDEN_PATH = Path(__file__).parent / "golden" / "synthetic_schemes.json"


def _cases() -> list[dict[str, Any]]:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


@pytest.mark.parametrize("case", _cases(), ids=lambda case: str(case["name"]))
def test_synthetic_golden_cases(case: dict[str, Any]) -> None:
    profile = BusinessProfile.model_validate(case["profile"])
    rule_set = SchemeRuleSet.model_validate(case["rule_set"])

    first = evaluate(profile, rule_set)
    second = evaluate(profile, rule_set)

    assert first == second
    assert first.decision == case["expected"]
    assert all(outcome.source_rule_id.startswith("synthetic-") for outcome in (
        *first.passed_rules,
        *first.failed_rules,
        *first.unknown_rules,
    ))

