from __future__ import annotations

from dataclasses import dataclass

from .privacy_change import (
    PrivacyChange,
    PrivacyChangeStatus,
)
from .privacy_change_registry import PrivacyChangeRegistry
from .privacy_governance_case import (
    PrivacyGovernanceCase,
    PrivacyTriggerType,
)
from .privacy_governance_case_service import PrivacyGovernanceCaseService
from .privacy_governance_gate import PrivacyGovernanceGate


@dataclass(frozen=True, slots=True)
class PrivacyGovernanceFlowResult:
    """Result of the Beta privacy-to-governance case flow."""

    change: PrivacyChange
    case: PrivacyGovernanceCase


class PrivacyGovernanceFlowService:
    """Orchestrate a privacy change into a governance case.

    Flow:

        Privacy Change
            ↓
        Privacy Governance Gate
            ↓
        Shared Change Registry
            ↓
        Privacy Governance Case Service
            ↓
        Shared Case Registry
            ↓
        Operations Center API
            ↓
        Operations Center UI

    The service does not make human governance decisions.
    """

    def __init__(
        self,
        *,
        change_registry: PrivacyChangeRegistry,
        governance_gate: PrivacyGovernanceGate,
        case_service: PrivacyGovernanceCaseService,
    ) -> None:
        if change_registry is None:
            raise ValueError(
                "change_registry cannot be None."
            )

        if governance_gate is None:
            raise ValueError(
                "governance_gate cannot be None."
            )

        if case_service is None:
            raise ValueError(
                "case_service cannot be None."
            )

        self._changes = change_registry
        self._gate = governance_gate
        self._cases = case_service

    def process_new_processing(
        self,
        change: PrivacyChange,
        *,
        automated_validation_passed: bool,
        case_id: str | None = None,
        trigger_source: str = "Processing Registry",
        processing_ids: tuple[str, ...] = (),
        data_map_ids: tuple[str, ...] = (),
    ) -> PrivacyGovernanceFlowResult:
        """Process a NEW_PROCESSING change through governance."""

        if change is None:
            raise ValueError(
                "change cannot be None."
            )

        #
        # Register the original change.
        #
        self._save_change(change)

        #
        # The governance gate is authoritative for the resulting
        # PrivacyChange status.
        #
        updated = self._gate.route(
            change,
            automated_validation_passed=automated_validation_passed,
        )

        #
        # Persist the authoritative gate result into the shared registry.
        #
        # This is important because PrivacyGovernanceCaseService reads
        # the authoritative PrivacyChange from this same registry.
        #
        self._save_change(updated)

        resolved_case_id = (
            case_id
            if case_id is not None
            else f"CASE-{updated.change_id}"
        )

        validation_status = (
            "PASS"
            if automated_validation_passed
            else "FAIL"
        )

        expected_governance_status = (
            self._expected_governance_status(
                updated.status
            )
        )

        case = self._cases.create_case(
            case_id=resolved_case_id,
            change_id=updated.change_id,
            trigger_type=PrivacyTriggerType.NEW_PROCESSING,
            trigger_source=trigger_source,
            validation_status=validation_status,
            processing_ids=processing_ids,
            data_map_ids=data_map_ids,
        )

        #
        # Defensive consistency boundary.
        #
        if case.governance_status != expected_governance_status:
            raise RuntimeError(
                "Privacy governance flow produced inconsistent state: "
                f"change status={updated.status.value}, "
                f"case governance status={case.governance_status}, "
                f"expected={expected_governance_status}."
            )

        return PrivacyGovernanceFlowResult(
            change=updated,
            case=case,
        )

    def _save_change(
        self,
        change: PrivacyChange,
    ) -> None:
        existing = self._changes.get(
            change.change_id
        )

        if existing is None:
            self._changes.register(
                change
            )
        else:
            self._changes.update(
                change
            )

    @staticmethod
    def _expected_governance_status(
        status: PrivacyChangeStatus,
    ) -> str:
        if status == PrivacyChangeStatus.BLOCKED:
            return "BLOCKED"

        if status == PrivacyChangeStatus.APPROVED:
            return "APPROVED"

        return "PENDING_DPO_GRC"


__all__ = [
    "PrivacyGovernanceFlowResult",
    "PrivacyGovernanceFlowService",
]