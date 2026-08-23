from __future__ import annotations

from dataclasses import dataclass

from .privacy_approval_email_service import PrivacyApprovalEmailService
from .privacy_approval_registry import PrivacyApprovalRegistry
from .privacy_change_registry import PrivacyChangeRegistry
from .privacy_governance_case_registry import PrivacyGovernanceCaseRegistry
from .privacy_governance_case_service import PrivacyGovernanceCaseService
from .privacy_governance_dashboard_service import PrivacyGovernanceDashboardService
from .privacy_governance_decision_service import PrivacyGovernanceDecisionService
from .privacy_governance_flow_service import PrivacyGovernanceFlowService
from .privacy_governance_gate import PrivacyGovernanceGate
from .privacy_validation_service import PrivacyValidationService


@dataclass(slots=True)
class PrivacyGovernanceComposition:
    """Single composition root for the privacy governance capability.

    Beta 1 uses in-memory registries. Application services receive those same
    instances so case creation, decisions, dashboard reads, and API reads all
    observe one coherent runtime state.

    Repository-backed implementations can replace the registries later without
    changing the API contract or frontend.
    """

    change_registry: PrivacyChangeRegistry
    case_registry: PrivacyGovernanceCaseRegistry
    approval_registry: PrivacyApprovalRegistry
    decision_service: PrivacyGovernanceDecisionService
    governance_gate: PrivacyGovernanceGate
    case_service: PrivacyGovernanceCaseService
    flow_service: PrivacyGovernanceFlowService
    dashboard_service: PrivacyGovernanceDashboardService


def create_privacy_governance_composition(
    *,
    validation_service: PrivacyValidationService | None = None,
    approval_email_service: PrivacyApprovalEmailService | None = None,
) -> PrivacyGovernanceComposition:
    """Create an isolated composition, primarily for tests and explicit DI."""

    change_registry = PrivacyChangeRegistry()
    case_registry = PrivacyGovernanceCaseRegistry()
    approval_registry = PrivacyApprovalRegistry()

    decision_service = PrivacyGovernanceDecisionService(
        approval_registry=approval_registry,
        change_registry=change_registry,
        case_registry=case_registry,
    )

    governance_gate = PrivacyGovernanceGate(
        registry=change_registry,
        validation_service=validation_service,
        approval_email_service=approval_email_service,
    )

    case_service = PrivacyGovernanceCaseService(
        case_registry=case_registry,
        change_registry=change_registry,
        approval_registry=approval_registry,
        decision_service=decision_service,
    )

    flow_service = PrivacyGovernanceFlowService(
        change_registry=change_registry,
        governance_gate=governance_gate,
        case_service=case_service,
    )

    dashboard_service = PrivacyGovernanceDashboardService(
        case_registry=case_registry,
        approval_registry=approval_registry,
    )

    return PrivacyGovernanceComposition(
        change_registry=change_registry,
        case_registry=case_registry,
        approval_registry=approval_registry,
        decision_service=decision_service,
        governance_gate=governance_gate,
        case_service=case_service,
        flow_service=flow_service,
        dashboard_service=dashboard_service,
    )


# Runtime composition boundary.
# The FastAPI adapter and application integrations must use this instance.
_runtime_composition: PrivacyGovernanceComposition | None = None


def get_privacy_governance_composition() -> PrivacyGovernanceComposition:
    """Return the process-wide Beta governance composition.

    This is the shared runtime instance used by the Operations Center API and
    by application integrations that submit privacy governance events.

    A future repository-backed implementation can keep this boundary while
    replacing the underlying registry adapters.
    """

    global _runtime_composition

    if _runtime_composition is None:
        _runtime_composition = create_privacy_governance_composition()

    return _runtime_composition


def reset_privacy_governance_composition_for_tests() -> None:
    """Reset the runtime composition.

    Intended for test isolation only. Production code must not reset runtime
    governance state.
    """

    global _runtime_composition
    _runtime_composition = None
