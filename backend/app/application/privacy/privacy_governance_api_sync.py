from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from .privacy_governance_case_service import PrivacyGovernanceCaseService
from .privacy_governance_excel_runtime_config import (
    get_privacy_governance_workbook_path,
)
from .privacy_governance_excel_sync import PrivacyGovernanceExcelSync
from .privacy_governance_runtime_sync import PrivacyGovernanceRuntimeSync

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GovernanceEvidenceSyncResult:
    """Result of a downstream Excel evidence projection."""

    status: str
    workbook_path: str
    error: str | None = None


class PrivacyGovernanceAPIEvidenceSync:
    """Coordinates post-decision Excel evidence projection.

    The governance decision is already authoritative before this component
    runs. A projection failure therefore does not rewrite governance state.
    It is surfaced explicitly so operations can detect evidence lag.
    """

    def __init__(
        self,
        *,
        case_service: PrivacyGovernanceCaseService,
        workbook_path: Path | None = None,
    ) -> None:
        self._case_service = case_service
        resolved_path = (
            workbook_path
            if workbook_path is not None
            else get_privacy_governance_workbook_path()
        )

        self._runtime_sync = PrivacyGovernanceRuntimeSync(
            case_service=case_service,
            excel_sync=PrivacyGovernanceExcelSync(
                workbook_path=resolved_path
            ),
        )
        self._workbook_path = Path(resolved_path)

    def sync_case(
        self,
        case_id: str,
    ) -> GovernanceEvidenceSyncResult:
        return self._run(
            lambda: self._runtime_sync.sync_case(case_id)
        )

    def sync_decision(
        self,
        case_id: str,
    ) -> GovernanceEvidenceSyncResult:
        return self._run(
            lambda: self._runtime_sync.sync_decision(case_id)
        )

    def _run(self, operation) -> GovernanceEvidenceSyncResult:
        try:
            operation()
        except Exception as exc:
            logger.exception(
                "Privacy governance Excel evidence synchronization failed."
            )
            return GovernanceEvidenceSyncResult(
                status="FAILED",
                workbook_path=str(self._workbook_path),
                error=str(exc),
            )

        return GovernanceEvidenceSyncResult(
            status="SYNCED",
            workbook_path=str(self._workbook_path),
        )


__all__ = [
    "GovernanceEvidenceSyncResult",
    "PrivacyGovernanceAPIEvidenceSync",
]
