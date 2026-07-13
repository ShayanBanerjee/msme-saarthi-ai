"""Table-driven coverage for every supported rule operator."""

from typing import Literal

import pytest

from eligibility_engine import BusinessProfile, EligibilityDecision, SchemeRuleSet, evaluate


def _rule_set(root: dict[str, object]) -> SchemeRuleSet:
    return SchemeRuleSet.model_validate(
        {
            "scheme_version_id": "synthetic-scheme-v1",
            "rule_set_version_id": "synthetic-rules-v1",
            "root": root,
        }
    )


@pytest.mark.parametrize(
    ("profile", "root", "expected"),
    [
        (
            {"state_code": "syn-a"},
            {
                "operator": "equals",
                "rule_id": "equals",
                "source_rule_id": "synthetic-source-equals",
                "field": "state_code",
                "value": "SYN-A",
            },
            "eligible",
        ),
        (
            {"sector_code": "SYN-MFG"},
            {
                "operator": "in",
                "rule_id": "in",
                "source_rule_id": "synthetic-source-in",
                "field": "sector_code",
                "values": ["SYN-SVC", "SYN-MFG"],
            },
            "eligible",
        ),
        (
            {"annual_turnover": "100.25"},
            {
                "operator": "less_than_or_equal",
                "rule_id": "lte",
                "source_rule_id": "synthetic-source-lte",
                "field": "annual_turnover",
                "value": "100.25",
            },
            "eligible",
        ),
        (
            {"years_in_operation": 2},
            {
                "operator": "greater_than_or_equal",
                "rule_id": "gte",
                "source_rule_id": "synthetic-source-gte",
                "field": "years_in_operation",
                "value": "3",
            },
            "ineligible",
        ),
        (
            {"employee_count": 10},
            {
                "operator": "between",
                "rule_id": "between",
                "source_rule_id": "synthetic-source-between",
                "field": "employee_count",
                "minimum": "10",
                "maximum": "20",
            },
            "eligible",
        ),
        (
            {"is_registered": False},
            {
                "operator": "exists",
                "rule_id": "exists",
                "source_rule_id": "synthetic-source-exists",
                "field": "is_registered",
            },
            "eligible",
        ),
    ],
)
def test_atomic_operators(
    profile: dict[str, object],
    root: dict[str, object],
    expected: Literal["eligible", "ineligible"],
) -> None:
    result = evaluate(BusinessProfile.model_validate(profile), _rule_set(root))

    assert result.decision == EligibilityDecision(expected)


@pytest.mark.parametrize(
    ("operator", "known_value", "expected"),
    [
        ("all", False, "ineligible"),
        ("all", True, "insufficient_information"),
        ("any", True, "eligible"),
        ("any", False, "insufficient_information"),
    ],
)
def test_all_and_any_use_strong_three_valued_logic(
    operator: Literal["all", "any"],
    known_value: bool,
    expected: Literal["eligible", "ineligible", "insufficient_information"],
) -> None:
    rules = _rule_set(
        {
            "operator": operator,
            "rule_id": "group",
            "source_rule_id": "synthetic-source-group",
            "rules": [
                {
                    "operator": "equals",
                    "rule_id": "known",
                    "source_rule_id": "synthetic-source-known",
                    "field": "is_registered",
                    "value": known_value,
                },
                {
                    "operator": "equals",
                    "rule_id": "unknown",
                    "source_rule_id": "synthetic-source-unknown",
                    "field": "state_code",
                    "value": "SYN-A",
                },
            ],
        }
    )

    result = evaluate(BusinessProfile(is_registered=True), rules)

    assert result.decision == EligibilityDecision(expected)


def test_not_preserves_unknown() -> None:
    rules = _rule_set(
        {
            "operator": "not",
            "rule_id": "not-group",
            "source_rule_id": "synthetic-source-not",
            "rule": {
                "operator": "equals",
                "rule_id": "missing",
                "source_rule_id": "synthetic-source-missing",
                "field": "state_code",
                "value": "SYN-A",
            },
        }
    )

    result = evaluate(BusinessProfile(), rules)

    assert result.decision is EligibilityDecision.INSUFFICIENT_INFORMATION
    assert [outcome.rule_id for outcome in result.unknown_rules] == ["missing", "not-group"]


def test_outcome_order_and_source_identifiers_are_deterministic() -> None:
    rules = _rule_set(
        {
            "operator": "all",
            "rule_id": "root",
            "source_rule_id": "synthetic-source-root",
            "rules": [
                {
                    "operator": "exists",
                    "rule_id": "first",
                    "source_rule_id": "synthetic-source-first",
                    "field": "state_code",
                },
                {
                    "operator": "exists",
                    "rule_id": "second",
                    "source_rule_id": "synthetic-source-second",
                    "field": "sector_code",
                },
            ],
        }
    )
    profile = BusinessProfile(state_code="SYN-A", sector_code="SYN-MFG")

    first = evaluate(profile, rules)
    second = evaluate(profile, rules)

    assert first == second
    assert [outcome.rule_id for outcome in first.passed_rules] == ["first", "second", "root"]
    assert [outcome.source_rule_id for outcome in first.passed_rules] == [
        "synthetic-source-first",
        "synthetic-source-second",
        "synthetic-source-root",
    ]

