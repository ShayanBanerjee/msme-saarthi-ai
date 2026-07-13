"""Typed inputs and outputs for deterministic eligibility evaluation."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Annotated, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

type ScalarValue = str | bool | int | Decimal
type RuleOperator = Literal[
    "equals",
    "in",
    "less_than_or_equal",
    "greater_than_or_equal",
    "between",
    "exists",
    "all",
    "any",
    "not",
]

MAX_RULE_DEPTH = 16
MAX_RULE_COUNT = 256


class ProfileField(StrEnum):
    """Allowlisted profile facts available to rules in engine schema v1."""

    STATE_CODE = "state_code"
    SECTOR_CODE = "sector_code"
    ENTERPRISE_CLASSIFICATION = "enterprise_classification"
    ANNUAL_TURNOVER = "annual_turnover"
    EMPLOYEE_COUNT = "employee_count"
    YEARS_IN_OPERATION = "years_in_operation"
    IS_REGISTERED = "is_registered"


class BusinessProfile(BaseModel):
    """Normalized, typed business facts; omitted values remain unknown."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    state_code: str | None = Field(default=None, min_length=1, max_length=32)
    sector_code: str | None = Field(default=None, min_length=1, max_length=64)
    enterprise_classification: str | None = Field(default=None, min_length=1, max_length=32)
    annual_turnover: Decimal | None = Field(default=None, ge=0, max_digits=24, decimal_places=4)
    employee_count: int | None = Field(default=None, ge=0)
    years_in_operation: int | None = Field(default=None, ge=0)
    is_registered: bool | None = None

    @field_validator("state_code", "sector_code", "enterprise_classification")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("profile codes must contain non-whitespace characters")
        return normalized

    @field_validator("employee_count", "years_in_operation", mode="before")
    @classmethod
    def require_exact_integer(cls, value: object) -> object:
        if isinstance(value, (bool, float, str)):
            raise ValueError("integer profile facts must be provided as integers")
        return value

    @field_validator("annual_turnover", mode="before")
    @classmethod
    def reject_float_money(cls, value: object) -> object:
        """Reject binary floats so monetary values originate from exact input."""
        if isinstance(value, (bool, float)):
            raise ValueError("annual_turnover must be provided as a decimal string or Decimal")
        return _validated_decimal(value, label="annual_turnover")

    def value_for(self, field: ProfileField) -> ScalarValue | None:
        """Read an allowlisted field without accepting arbitrary paths."""
        value = cast(ScalarValue | None, getattr(self, field.value))
        if value is None:
            return None
        return value


class RuleBase(BaseModel):
    """Fields shared by atomic and composite rules."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")
    source_rule_id: str = Field(min_length=1, max_length=256)


class EqualsRule(RuleBase):
    operator: Literal["equals"]
    field: ProfileField
    value: ScalarValue

    @model_validator(mode="before")
    @classmethod
    def normalize_numeric_value(cls, data: object) -> object:
        return _normalize_comparison_data(data, "value")


class InRule(RuleBase):
    operator: Literal["in"]
    field: ProfileField
    values: tuple[ScalarValue, ...] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_numeric_values(cls, data: object) -> object:
        if not isinstance(data, dict) or data.get("field") not in _NUMERIC_FIELD_VALUES:
            return data
        normalized = dict(data)
        values = normalized.get("values")
        if isinstance(values, (list, tuple)):
            normalized["values"] = tuple(_exact_decimal(value) for value in values)
        return normalized

    @field_validator("values")
    @classmethod
    def values_are_unique(cls, values: tuple[ScalarValue, ...]) -> tuple[ScalarValue, ...]:
        if len(set(values)) != len(values):
            raise ValueError("in values must be unique")
        return values


class LessThanOrEqualRule(RuleBase):
    operator: Literal["less_than_or_equal"]
    field: ProfileField
    value: Decimal

    @field_validator("value", mode="before")
    @classmethod
    def exact_value(cls, value: object) -> object:
        return _exact_decimal(value)


class GreaterThanOrEqualRule(RuleBase):
    operator: Literal["greater_than_or_equal"]
    field: ProfileField
    value: Decimal

    @field_validator("value", mode="before")
    @classmethod
    def exact_value(cls, value: object) -> object:
        return _exact_decimal(value)


class BetweenRule(RuleBase):
    operator: Literal["between"]
    field: ProfileField
    minimum: Decimal
    maximum: Decimal

    @field_validator("minimum", "maximum", mode="before")
    @classmethod
    def exact_bound(cls, value: object) -> object:
        return _exact_decimal(value)

    @model_validator(mode="after")
    def ordered_bounds(self) -> BetweenRule:
        if self.minimum > self.maximum:
            raise ValueError("between minimum must be less than or equal to maximum")
        return self


class ExistsRule(RuleBase):
    operator: Literal["exists"]
    field: ProfileField


class AllRule(RuleBase):
    operator: Literal["all"]
    rules: tuple[RuleNode, ...] = Field(min_length=1)


class AnyRule(RuleBase):
    operator: Literal["any"]
    rules: tuple[RuleNode, ...] = Field(min_length=1)


class NotRule(RuleBase):
    operator: Literal["not"]
    rule: RuleNode


type RuleNode = Annotated[
    EqualsRule
    | InRule
    | LessThanOrEqualRule
    | GreaterThanOrEqualRule
    | BetweenRule
    | ExistsRule
    | AllRule
    | AnyRule
    | NotRule,
    Field(discriminator="operator"),
]

AllRule.model_rebuild()
AnyRule.model_rebuild()
NotRule.model_rebuild()

_NUMERIC_FIELDS = {
    ProfileField.ANNUAL_TURNOVER,
    ProfileField.EMPLOYEE_COUNT,
    ProfileField.YEARS_IN_OPERATION,
}
_NUMERIC_FIELD_VALUES = {field.value for field in _NUMERIC_FIELDS}
_STRING_FIELDS = {
    ProfileField.STATE_CODE,
    ProfileField.SECTOR_CODE,
    ProfileField.ENTERPRISE_CLASSIFICATION,
}


def _exact_decimal(value: object) -> object:
    if isinstance(value, (bool, float)):
        raise ValueError("numeric rule values must use an integer, decimal string, or Decimal")
    return _validated_decimal(value, label="numeric rule value")


def _validated_decimal(value: object, *, label: str) -> object:
    if not isinstance(value, (str, int, Decimal)):
        return value
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"{label} must be a valid decimal") from error
    if not parsed.is_finite():
        raise ValueError(f"{label} must be finite")
    return parsed


def _normalize_comparison_data(data: object, key: str) -> object:
    if not isinstance(data, dict) or data.get("field") not in _NUMERIC_FIELD_VALUES:
        return data
    normalized = dict(data)
    if key in normalized:
        normalized[key] = _exact_decimal(normalized[key])
    return normalized


class SchemeRuleSet(BaseModel):
    """Immutable, versioned root rule and its evidence-facing identifiers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scheme_version_id: str = Field(min_length=1, max_length=128)
    rule_set_version_id: str = Field(min_length=1, max_length=128)
    root: RuleNode

    @model_validator(mode="after")
    def validate_semantics(self) -> SchemeRuleSet:
        seen: set[str] = set()
        rule_count = 0

        def visit(rule: RuleNode, *, depth: int) -> None:
            nonlocal rule_count
            rule_count += 1
            if rule_count > MAX_RULE_COUNT:
                raise ValueError(f"rule set cannot contain more than {MAX_RULE_COUNT} rules")
            if depth > MAX_RULE_DEPTH:
                raise ValueError(f"rule set cannot exceed depth {MAX_RULE_DEPTH}")
            if rule.rule_id in seen:
                raise ValueError(f"duplicate rule_id: {rule.rule_id}")
            seen.add(rule.rule_id)
            if isinstance(
                rule, (LessThanOrEqualRule, GreaterThanOrEqualRule, BetweenRule)
            ) and rule.field not in _NUMERIC_FIELDS:
                raise ValueError(f"operator {rule.operator} requires a numeric profile field")
            if isinstance(rule, (EqualsRule, InRule)):
                values = (rule.value,) if isinstance(rule, EqualsRule) else rule.values
                if rule.field in _STRING_FIELDS and any(
                    not isinstance(value, str) for value in values
                ):
                    raise ValueError(f"field {rule.field} requires string comparison values")
                if rule.field is ProfileField.IS_REGISTERED and any(
                    not isinstance(value, bool) for value in values
                ):
                    raise ValueError("field is_registered requires boolean comparison values")
                if rule.field in _NUMERIC_FIELDS and any(
                    isinstance(value, bool) or not isinstance(value, (int, Decimal))
                    for value in values
                ):
                    raise ValueError(f"field {rule.field} requires numeric comparison values")
            if isinstance(rule, (AllRule, AnyRule)):
                for child in rule.rules:
                    visit(child, depth=depth + 1)
            elif isinstance(rule, NotRule):
                visit(rule.rule, depth=depth + 1)

        visit(self.root, depth=1)
        return self


class RuleStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"


class EligibilityDecision(StrEnum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class RuleOutcome(BaseModel):
    """One stable rule result with its source rule identifier."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str
    source_rule_id: str
    operator: RuleOperator
    status: RuleStatus


class EligibilityResult(BaseModel):
    """Complete deterministic result ordered by rule evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scheme_version_id: str
    rule_set_version_id: str
    decision: EligibilityDecision
    passed_rules: tuple[RuleOutcome, ...]
    failed_rules: tuple[RuleOutcome, ...]
    unknown_rules: tuple[RuleOutcome, ...]
