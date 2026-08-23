from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetentionRule:
    retention_id: str
    data_domain: str
    record_type: str
    retention_period: str
    trigger: str
    deletion_action: str
    legal_policy_basis: str


class RetentionRegistry:
    def __init__(self, rules: list[RetentionRule] | None = None) -> None:
        self._rules = {rule.retention_id: rule for rule in rules or []}

    def register(self, rule: RetentionRule) -> None:
        if rule.retention_id in self._rules:
            raise ValueError(
                f"Retention rule already registered: {rule.retention_id}"
            )
        self._rules[rule.retention_id] = rule

    def get(self, retention_id: str) -> RetentionRule:
        return self._rules[retention_id]

    def all(self) -> tuple[RetentionRule, ...]:
        return tuple(self._rules.values())
