from __future__ import annotations

from .privacy_governance_case import PrivacyGovernanceCase


class PrivacyGovernanceCaseRegistry:
    """Beta registry for privacy governance cases."""

    def __init__(
        self,
        cases: list[PrivacyGovernanceCase] | None = None,
    ) -> None:
        self._cases: dict[str, PrivacyGovernanceCase] = {}
        for case in cases or []:
            self.register(case)

    def register(self, case: PrivacyGovernanceCase) -> None:
        if case.case_id in self._cases:
            raise ValueError(f"Case already registered: {case.case_id}")
        self._cases[case.case_id] = case

    def get(self, case_id: str) -> PrivacyGovernanceCase:
        try:
            return self._cases[case_id]
        except KeyError as exc:
            raise KeyError(f"Governance case not found: {case_id}") from exc

    def update(self, case: PrivacyGovernanceCase) -> None:
        if case.case_id not in self._cases:
            raise KeyError(f"Governance case not found: {case.case_id}")
        self._cases[case.case_id] = case

    def all(self) -> tuple[PrivacyGovernanceCase, ...]:
        return tuple(self._cases.values())

    def pending(self) -> tuple[PrivacyGovernanceCase, ...]:
        return tuple(
            case
            for case in self._cases.values()
            if case.governance_status == "PENDING_DPO_GRC"
        )
