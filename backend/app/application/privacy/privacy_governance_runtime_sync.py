from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .privacy_governance_case import PrivacyGovernanceCase
from .privacy_governance_case_service import PrivacyGovernanceCaseService


@runtime_checkable
class GovernanceExcelSyncPort(Protocol):
    """Port for projecting authoritative governance state to Excel."""

    def sync_all(
        self,
        *,
        case_registry: object,
        approval_registry: object,
    ) -> None:
        ...

    def sync_case(self, case: PrivacyGovernanceCase) -> None:
        ...

    def sync_approval(self, case_id: str) -> None:
        ...


@dataclass(slots=True)
class PrivacyGovernanceRuntimeSync:
    """Project authoritative governance state into the Excel evidence layer.

    Governance registries remain the source of truth. Excel is a downstream
    projection and never participates in governance decisions.
    """

    case_service: PrivacyGovernanceCaseService
    excel_sync: GovernanceExcelSyncPort

    def sync_case(self, case_id: str) -> PrivacyGovernanceCase:
        case = self.case_service.get_case(case_id)

        if self._supports_bulk_sync():
            self._sync_all()
        else:
            self.excel_sync.sync_case(case)

        return case

    def sync_decision(self, case_id: str) -> PrivacyGovernanceCase:
        case = self.case_service.get_case(case_id)

        if self._supports_bulk_sync():
            self._sync_all()
        else:
            self.excel_sync.sync_case(case)
            self.excel_sync.sync_approval(case_id)

        return case

    def _supports_bulk_sync(self) -> bool:
        return callable(getattr(self.excel_sync, "sync_all", None))

    def _sync_all(self) -> None:
        sync_all = getattr(self.excel_sync, "sync_all", None)
        if not callable(sync_all):
            raise TypeError(
                "Configured Excel synchronizer does not implement sync_all()."
            )

        sync_all(
            case_registry=self.case_service.case_registry,
            approval_registry=self.case_service.approval_registry,
        )


__all__ = ["GovernanceExcelSyncPort", "PrivacyGovernanceRuntimeSync"]
