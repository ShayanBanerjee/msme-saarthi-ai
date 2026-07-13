"""Focused eligibility rule semantics and validation tests."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from eligibility_engine import (
    BusinessProfile,
    EligibilityDecision,
    RuleStatus,
    SchemeRuleSet,
    evaluate,
)


def test_missing_field_is_unknown_not_failed() -> None:
    rules = SchemeRuleSet.model_validate(
        {
            "scheme_version_id": "synthetic-v1",
            "rule_set_version_id": "synthetic-r1",
            "root": {
                "operator": "equals",
                "rule_id": "registration",
                "source_rule_id": "synthetic-source-registration",
                "field": "is_registered",
                "value": True,
            },
        }
    )

    result = evaluate(BusinessProfile(), rules)

    assert result.decision is EligibilityDecision.INSUFFICIENT_INFORMATION
    assert result.failed_rules == ()
    assert result.unknown_rules[0].status is RuleStatus.UNKNOWN


def test_money_uses_exact_decimal_boundary() -> None:
    rules = SchemeRuleSet.model_validate(
        {
            "scheme_version_id": "synthetic-v1",
            "rule_set_version_id": "synthetic-r1",
            "root": {
                "operator": "less_than_or_equal",
                "rule_id": "turnover-limit",
                "source_rule_id": "synthetic-source-turnover",
                "field": "annual_turnover",
                "value": "0.30",
            },
        }
    )

    profile = BusinessProfile(annual_turnover=Decimal("0.10") + Decimal("0.20"))
    result = evaluate(profile, rules)

    assert profile.annual_turnover == Decimal("0.30")
    assert result.decision is EligibilityDecision.ELIGIBLE


def test_float_money_is_rejected() -> None:
    with pytest.raises(ValidationError, match="decimal string or Decimal"):
        BusinessProfile(annual_turnover=0.1)


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_money_and_thresholds_are_rejected(value: str) -> None:
    with pytest.raises(ValidationError, match="finite"):
        BusinessProfile(annual_turnover=value)

    with pytest.raises(ValidationError, match="finite"):
        SchemeRuleSet.model_validate(
            {
                "scheme_version_id": "synthetic-v1",
                "rule_set_version_id": "synthetic-r1",
                "root": {
                    "operator": "less_than_or_equal",
                    "rule_id": "turnover",
                    "source_rule_id": "synthetic-source",
                    "field": "annual_turnover",
                    "value": value,
                },
            }
        )


@pytest.mark.parametrize("field", ["employee_count", "years_in_operation"])
@pytest.mark.parametrize("value", [True, 1.0, "1"])
def test_integer_profile_facts_reject_ambiguous_coercion(field: str, value: object) -> None:
    with pytest.raises(ValidationError, match="provided as integers"):
        BusinessProfile.model_validate({field: value})


@pytest.mark.parametrize(
    "root, message",
    [
        (
            {
                "operator": "between",
                "rule_id": "bad-bounds",
                "source_rule_id": "synthetic-source",
                "field": "employee_count",
                "minimum": "10",
                "maximum": "5",
            },
            "minimum",
        ),
        (
            {
                "operator": "less_than_or_equal",
                "rule_id": "bad-field",
                "source_rule_id": "synthetic-source",
                "field": "state_code",
                "value": "10",
            },
            "numeric profile field",
        ),
    ],
)
def test_invalid_rules_fail_validation(root: dict[str, object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        SchemeRuleSet.model_validate(
            {
                "scheme_version_id": "synthetic-v1",
                "rule_set_version_id": "synthetic-r1",
                "root": root,
            }
        )


def test_duplicate_rule_ids_and_duplicate_in_values_fail_validation() -> None:
    with pytest.raises(ValidationError, match="duplicate rule_id"):
        SchemeRuleSet.model_validate(
            {
                "scheme_version_id": "synthetic-v1",
                "rule_set_version_id": "synthetic-r1",
                "root": {
                    "operator": "all",
                    "rule_id": "duplicate",
                    "source_rule_id": "synthetic-source-root",
                    "rules": [
                        {
                            "operator": "exists",
                            "rule_id": "duplicate",
                            "source_rule_id": "synthetic-source-child",
                            "field": "state_code",
                        }
                    ],
                },
            }
        )

    with pytest.raises(ValidationError, match="values must be unique"):
        SchemeRuleSet.model_validate(
            {
                "scheme_version_id": "synthetic-v1",
                "rule_set_version_id": "synthetic-r1",
                "root": {
                    "operator": "in",
                    "rule_id": "duplicate-values",
                    "source_rule_id": "synthetic-source",
                    "field": "annual_turnover",
                    "values": ["1.0", "1.00"],
                },
            }
        )


def test_rule_tree_depth_is_bounded() -> None:
    root: dict[str, object] = {
        "operator": "exists",
        "rule_id": "leaf",
        "source_rule_id": "synthetic-source-leaf",
        "field": "state_code",
    }
    for index in range(16):
        root = {
            "operator": "not",
            "rule_id": f"not-{index}",
            "source_rule_id": f"synthetic-source-not-{index}",
            "rule": root,
        }

    with pytest.raises(ValidationError, match="cannot exceed depth 16"):
        SchemeRuleSet.model_validate(
            {
                "scheme_version_id": "synthetic-v1",
                "rule_set_version_id": "synthetic-r1",
                "root": root,
            }
        )


@pytest.mark.parametrize(
    "root",
    [
        {
            "operator": "all",
            "rule_id": "empty",
            "source_rule_id": "synthetic-source-empty",
            "rules": [],
        },
        {
            "operator": "execute_text",
            "rule_id": "unsupported",
            "source_rule_id": "synthetic-source-unsupported",
            "field": "state_code",
            "value": "SYN-A",
        },
    ],
)
def test_empty_groups_and_unknown_operators_fail_validation(root: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        SchemeRuleSet.model_validate(
            {
                "scheme_version_id": "synthetic-v1",
                "rule_set_version_id": "synthetic-r1",
                "root": root,
            }
        )


def test_rule_count_is_bounded() -> None:
    rules = [
        {
            "operator": "exists",
            "rule_id": f"rule-{index}",
            "source_rule_id": f"synthetic-source-{index}",
            "field": "state_code",
        }
        for index in range(256)
    ]

    with pytest.raises(ValidationError, match="cannot contain more than 256 rules"):
        SchemeRuleSet.model_validate(
            {
                "scheme_version_id": "synthetic-v1",
                "rule_set_version_id": "synthetic-r1",
                "root": {
                    "operator": "all",
                    "rule_id": "root",
                    "source_rule_id": "synthetic-source-root",
                    "rules": rules,
                },
            }
        )
