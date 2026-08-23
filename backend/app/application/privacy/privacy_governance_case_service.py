from __future__ import annotations

from datetime import datetime, timezone

from .privacy_approval_record import (
    ApprovalDecision,
    PrivacyApprovalRecord,
)
from .privacy_approval_registry import PrivacyApprovalRegistry
from .privacy_change import (
    PrivacyChange,
    PrivacyChangeStatus,
)
from .privacy_change_registry import PrivacyChangeRegistry
from .privacy_governance_case import (
    PrivacyGovernanceCase,
    PrivacyTriggerType,
)
from .privacy_governance_case_registry import (
    PrivacyGovernanceCaseRegistry,
)
from .privacy_governance_decision_service import (
    PrivacyGovernanceDecisionService,
)


class PrivacyGovernanceCaseService:
    """Application service for privacy governance cases.

    This service is the application boundary between privacy processing and
    the case-centric governance model rendered by the Operations Center.

    It owns no persistence. Registries are injected so Beta can use in-memory
    state while the same contracts can later be backed by repositories.

    The registries remain authoritative. Downstream adapters such as the
    Excel evidence synchronizer receive read-only access to these same
    registry instances and must never create a second governance state store.
    """

    def __init__(
        self,
        *,
        case_registry: PrivacyGovernanceCaseRegistry,
        change_registry: PrivacyChangeRegistry,
        approval_registry: PrivacyApprovalRegistry,
        decision_service: PrivacyGovernanceDecisionService,
    ) -> None:
        if case_registry is None:
            raise ValueError("case_registry cannot be None.")

        if change_registry is None:
            raise ValueError("change_registry cannot be None.")

        if approval_registry is None:
            raise ValueError("approval_registry cannot be None.")

        if decision_service is None:
            raise ValueError("decision_service cannot be None.")

        self._cases = case_registry
        self._changes = change_registry
        self._approvals = approval_registry
        self._decision_service = decision_service

    @property
    def case_registry(self) -> PrivacyGovernanceCaseRegistry:
        """Return the authoritative governance case registry."""

        return self._cases

    @property
    def change_registry(self) -> PrivacyChangeRegistry:
        """Return the authoritative privacy change registry."""

        return self._changes

    @property
    def approval_registry(self) -> PrivacyApprovalRegistry:
        """Return the authoritative approval evidence registry."""

        return self._approvals

    def create_case(
        self,
        *,
        case_id: str,
        change_id: str,
        trigger_type: PrivacyTriggerType,
        trigger_source: str,
        validation_status: str = "PENDING",
        email_status: str = "NOT_SENT",
        processing_ids: tuple[str, ...] = (),
        data_map_ids: tuple[str, ...] = (),
    ) -> PrivacyGovernanceCase:
        """Create a governance case from a registered privacy change.

        The authoritative PrivacyChange status determines the initial
        governance case status.

        Status mapping:

            PrivacyChangeStatus.APPROVED
                -> APPROVED

            PrivacyChangeStatus.BLOCKED
                -> BLOCKED

            PrivacyChangeStatus.PENDING_DPO_GRC
                -> PENDING_DPO_GRC

        The enum is compared directly rather than comparing ``.value`` to
        hard-coded uppercase strings. This is important because the
        PrivacyChangeStatus values are lowercase.
        """

        self._require_text(
            "case_id",
            case_id,
        )

        self._require_text(
            "change_id",
            change_id,
        )

        self._require_text(
            "trigger_source",
            trigger_source,
        )

        existing = (
            self._cases.get(case_id)
            if self._case_exists(case_id)
            else None
        )

        if existing is not None:
            return existing

        change = self._changes.get(
            change_id
        )

        if change is None:
            raise KeyError(
                f"Privacy change not found: {change_id}"
            )

        #
        # IMPORTANT:
        #
        # Compare the authoritative enum directly.
        #
        # Do NOT use:
        #
        #     change.status.value == "BLOCKED"
        #
        # because PrivacyChangeStatus.BLOCKED.value is "blocked".
        #

        if change.status == PrivacyChangeStatus.BLOCKED:
            governance_status = "BLOCKED"

        elif change.status == PrivacyChangeStatus.APPROVED:
            governance_status = "APPROVED"

        else:
            governance_status = "PENDING_DPO_GRC"

        case = PrivacyGovernanceCase(
            case_id=case_id,
            title=change.title,
            summary=change.description,
            trigger_type=trigger_type,
            triggered_at=datetime.now(timezone.utc),
            trigger_source=trigger_source,
            change_id=change_id,
            processing_ids=processing_ids,
            data_map_ids=data_map_ids,
            risk=change.risk.value,
            validation_status=validation_status,
            email_status=email_status,
            governance_status=governance_status,
        )

        self._cases.register(
            case
        )

        return case

    def get_case(
        self,
        case_id: str,
    ) -> PrivacyGovernanceCase:
        """Return one authoritative governance case."""

        self._require_text(
            "case_id",
            case_id,
        )

        return self._cases.get(
            case_id
        )

    def list_cases(
        self,
    ) -> tuple[PrivacyGovernanceCase, ...]:
        """Return all authoritative governance cases."""

        return self._cases.all()

    def list_pending_cases(
        self,
    ) -> tuple[PrivacyGovernanceCase, ...]:
        """Return all governance cases awaiting human review."""

        return self._cases.pending()

    def get_approval_history(
        self,
        case_id: str,
    ) -> tuple[PrivacyApprovalRecord, ...]:
        """Return authoritative approval evidence for a case."""

        self._require_text(
            "case_id",
            case_id,
        )

        self._cases.get(
            case_id
        )

        return self._approvals.for_case(
            case_id
        )

    def approve(
        self,
        *,
        case_id: str,
        change_id: str,
        approval_id: str,
        reviewer: str,
        role: str,
        comment: str,
    ) -> PrivacyApprovalRecord:
        """Record an explicit human approval."""

        self._validate_decision_inputs(
            case_id=case_id,
            change_id=change_id,
            reviewer=reviewer,
            role=role,
        )

        return self._decision_service.record_decision(
            case_id=case_id,
            change_id=change_id,
            approval_id=approval_id,
            reviewer=reviewer,
            role=role,
            decision=ApprovalDecision.APPROVED,
            comment=comment,
        )

    def reject(
        self,
        *,
        case_id: str,
        change_id: str,
        approval_id: str,
        reviewer: str,
        role: str,
        comment: str,
    ) -> PrivacyApprovalRecord:
        """Record an explicit human rejection."""

        self._validate_decision_inputs(
            case_id=case_id,
            change_id=change_id,
            reviewer=reviewer,
            role=role,
        )

        return self._decision_service.record_decision(
            case_id=case_id,
            change_id=change_id,
            approval_id=approval_id,
            reviewer=reviewer,
            role=role,
            decision=ApprovalDecision.REJECTED,
            comment=comment,
        )

    def request_changes(
        self,
        *,
        case_id: str,
        change_id: str,
        approval_id: str,
        reviewer: str,
        role: str,
        comment: str,
    ) -> PrivacyApprovalRecord:
        """Record an explicit request-for-changes decision."""

        self._validate_decision_inputs(
            case_id=case_id,
            change_id=change_id,
            reviewer=reviewer,
            role=role,
        )

        return self._decision_service.record_decision(
            case_id=case_id,
            change_id=change_id,
            approval_id=approval_id,
            reviewer=reviewer,
            role=role,
            decision=ApprovalDecision.REQUEST_CHANGES,
            comment=comment,
        )

    def _validate_decision_inputs(
        self,
        *,
        case_id: str,
        change_id: str,
        reviewer: str,
        role: str,
    ) -> None:
        """Validate the context required for a human decision."""

        self._require_text(
            "case_id",
            case_id,
        )

        self._require_text(
            "change_id",
            change_id,
        )

        self._require_text(
            "reviewer",
            reviewer,
        )

        self._cases.get(
            case_id
        )

        change = self._changes.get(
            change_id
        )

        if change is None:
            raise KeyError(
                f"Privacy change not found: {change_id}"
            )

        self._require_text(
            "role",
            role,
        )

    def _case_exists(
        self,
        case_id: str,
    ) -> bool:
        """Return whether a case exists."""

        try:
            self._cases.get(
                case_id
            )

        except KeyError:
            return False

        return True

    @staticmethod
    def _require_text(
        field_name: str,
        value: str,
    ) -> None:
        """Validate a required text field."""

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{field_name} is required."
            )