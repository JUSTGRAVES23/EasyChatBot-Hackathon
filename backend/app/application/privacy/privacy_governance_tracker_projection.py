from __future__ import annotations

from typing import Any

from .privacy_governance_excel_sync import PrivacyGovernanceExcelSync


class PrivacyGovernanceTrackerProjection:
    """Application boundary for projecting shared governance state."""

    def __init__(
        self,
        *,
        sync: PrivacyGovernanceExcelSync,
        case_registry: Any,
        approval_registry: Any,
    ) -> None:
        if sync is None:
            raise ValueError("sync cannot be None.")
        if case_registry is None:
            raise ValueError("case_registry cannot be None.")
        if approval_registry is None:
            raise ValueError("approval_registry cannot be None.")

        self._sync = sync
        self._cases = case_registry
        self._approvals = approval_registry

    def sync(self) -> None:
        self._sync.sync_all(
            case_registry=self._cases,
            approval_registry=self._approvals,
        )
