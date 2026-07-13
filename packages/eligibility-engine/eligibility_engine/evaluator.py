"""Pure deterministic evaluation over validated model inputs."""

from decimal import Decimal

from eligibility_engine.models import (
    AllRule,
    AnyRule,
    BetweenRule,
    BusinessProfile,
    EligibilityDecision,
    EligibilityResult,
    EqualsRule,
    ExistsRule,
    GreaterThanOrEqualRule,
    InRule,
    LessThanOrEqualRule,
    NotRule,
    RuleNode,
    RuleOutcome,
    RuleStatus,
    SchemeRuleSet,
)


def _as_decimal(value: object) -> Decimal:
    if isinstance(value, bool):
        raise TypeError("booleans are not numeric profile facts")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    raise TypeError("comparison requires a numeric profile fact")


def _atomic_status(rule: RuleNode, profile: BusinessProfile) -> RuleStatus:
    if isinstance(rule, (AllRule, AnyRule, NotRule)):
        raise TypeError("composite rules are evaluated separately")

    actual = profile.value_for(rule.field)
    if actual is None:
        return RuleStatus.UNKNOWN
    if isinstance(rule, ExistsRule):
        return RuleStatus.PASSED
    if isinstance(rule, EqualsRule):
        return RuleStatus.PASSED if actual == rule.value else RuleStatus.FAILED
    if isinstance(rule, InRule):
        return RuleStatus.PASSED if actual in rule.values else RuleStatus.FAILED

    numeric_actual = _as_decimal(actual)
    if isinstance(rule, LessThanOrEqualRule):
        matched = numeric_actual <= rule.value
    elif isinstance(rule, GreaterThanOrEqualRule):
        matched = numeric_actual >= rule.value
    elif isinstance(rule, BetweenRule):
        matched = rule.minimum <= numeric_actual <= rule.maximum
    else:
        raise TypeError(f"unsupported rule type: {type(rule).__name__}")
    return RuleStatus.PASSED if matched else RuleStatus.FAILED


def _evaluate_rule(
    rule: RuleNode, profile: BusinessProfile, outcomes: list[RuleOutcome]
) -> RuleStatus:
    if isinstance(rule, AllRule):
        child_statuses = [_evaluate_rule(child, profile, outcomes) for child in rule.rules]
        if RuleStatus.FAILED in child_statuses:
            status = RuleStatus.FAILED
        elif RuleStatus.UNKNOWN in child_statuses:
            status = RuleStatus.UNKNOWN
        else:
            status = RuleStatus.PASSED
    elif isinstance(rule, AnyRule):
        child_statuses = [_evaluate_rule(child, profile, outcomes) for child in rule.rules]
        if RuleStatus.PASSED in child_statuses:
            status = RuleStatus.PASSED
        elif RuleStatus.UNKNOWN in child_statuses:
            status = RuleStatus.UNKNOWN
        else:
            status = RuleStatus.FAILED
    elif isinstance(rule, NotRule):
        child_status = _evaluate_rule(rule.rule, profile, outcomes)
        status = {
            RuleStatus.PASSED: RuleStatus.FAILED,
            RuleStatus.FAILED: RuleStatus.PASSED,
            RuleStatus.UNKNOWN: RuleStatus.UNKNOWN,
        }[child_status]
    else:
        status = _atomic_status(rule, profile)

    outcomes.append(
        RuleOutcome(
            rule_id=rule.rule_id,
            source_rule_id=rule.source_rule_id,
            operator=rule.operator,
            status=status,
        )
    )
    return status


def evaluate(profile: BusinessProfile, rule_set: SchemeRuleSet) -> EligibilityResult:
    """Evaluate validated inputs with strong three-valued logic."""
    outcomes: list[RuleOutcome] = []
    root_status = _evaluate_rule(rule_set.root, profile, outcomes)
    decision = {
        RuleStatus.PASSED: EligibilityDecision.ELIGIBLE,
        RuleStatus.FAILED: EligibilityDecision.INELIGIBLE,
        RuleStatus.UNKNOWN: EligibilityDecision.INSUFFICIENT_INFORMATION,
    }[root_status]
    return EligibilityResult(
        scheme_version_id=rule_set.scheme_version_id,
        rule_set_version_id=rule_set.rule_set_version_id,
        decision=decision,
        passed_rules=tuple(item for item in outcomes if item.status is RuleStatus.PASSED),
        failed_rules=tuple(item for item in outcomes if item.status is RuleStatus.FAILED),
        unknown_rules=tuple(item for item in outcomes if item.status is RuleStatus.UNKNOWN),
    )

