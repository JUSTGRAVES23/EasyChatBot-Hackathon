from __future__ import annotations

import os
from dataclasses import dataclass

from .privacy_approval_email_service import (
    ApprovalEmailSender,
    PrivacyApprovalEmailService,
)
from .privacy_approval_registry import PrivacyApprovalRegistry
from .privacy_change_registry import PrivacyChangeRegistry
from .privacy_governance_case_registry import (
    PrivacyGovernanceCaseRegistry,
)
from .privacy_governance_case_service import (
    PrivacyGovernanceCaseService,
)
from .privacy_governance_dashboard_service import (
    PrivacyGovernanceDashboardService,
)
from .privacy_governance_decision_service import (
    PrivacyGovernanceDecisionService,
)
from .privacy_governance_flow_service import (
    PrivacyGovernanceFlowService,
)
from .privacy_governance_gate import (
    PrivacyGovernanceGate,
)
from .privacy_validation_service import (
    PrivacyValidationService,
)


@dataclass(slots=True)
class PrivacyGovernanceComposition:
    """Single composition root for the privacy governance capability.

    Beta 1 uses in-memory registries.

    All application services receive the same registry instances so that:

    - case creation;
    - governance decisions;
    - approval history;
    - dashboard reads;
    - API reads

    operate on one coherent runtime state.

    Email infrastructure is optional at composition-construction time.
    This is intentional:

    - unit tests must not require external email configuration;
    - application startup must not fail merely because email is disabled;
    - actual escalation requires an explicitly configured email service.

    Repository-backed implementations can replace the registries later
    without changing the application service contracts.
    """

    change_registry: PrivacyChangeRegistry
    case_registry: PrivacyGovernanceCaseRegistry
    approval_registry: PrivacyApprovalRegistry

    decision_service: PrivacyGovernanceDecisionService
    governance_gate: PrivacyGovernanceGate
    case_service: PrivacyGovernanceCaseService
    flow_service: PrivacyGovernanceFlowService
    dashboard_service: PrivacyGovernanceDashboardService


def _build_runtime_approval_email_service(
    *,
    approval_email_service: PrivacyApprovalEmailService | None,
) -> PrivacyApprovalEmailService | None:
    """Resolve the optional runtime approval-email service.

    Explicit dependency injection always wins.

    When no service is injected, the service is constructed only when
    the required runtime configuration exists.

    Missing email configuration is NOT a composition-construction error.

    This is important because the privacy governance application layer
    must remain usable without an external email provider, especially in:

    - unit tests;
    - local development;
    - provider-independent deployments;
    - environments where email escalation is intentionally disabled.

    Actual governance escalation remains protected by
    PrivacyGovernanceGate.route_and_escalate(), which requires an
    approval email service before attempting delivery.
    """

    if approval_email_service is not None:
        return approval_email_service

    recipient = os.getenv(
        "PRIVACY_APPROVAL_EMAIL_TO",
        "",
    ).strip()

    if not recipient:
        return None

    try:
        from backend.app.infrastructure.email.resend_approval_email_sender import (
            ResendApprovalEmailSender,
        )
    except ImportError:
        # Keep the application composition provider-independent.
        #
        # Infrastructure may not be installed in lightweight unit-test
        # environments.
        return None

    try:
        sender: ApprovalEmailSender = ResendApprovalEmailSender()
    except (RuntimeError, ValueError):
        # Configuration/provider availability must not prevent creation
        # of the governance application composition.
        return None

    return PrivacyApprovalEmailService(
        sender=sender,
        approval_recipient=recipient,
    )


def create_privacy_governance_composition(
    *,
    validation_service: PrivacyValidationService | None = None,
    approval_email_service: PrivacyApprovalEmailService | None = None,
) -> PrivacyGovernanceComposition:
    """Create an isolated privacy governance composition.

    This function is the primary dependency-injection boundary.

    Important design rule:

        Composition creation != external side effect.

    Creating this composition:

    - creates registries;
    - wires application services;
    - optionally wires configured infrastructure;

    but does NOT:

    - send email;
    - call Resend;
    - make governance decisions;
    - modify production systems.
    """

    # ------------------------------------------------------------------
    # Authoritative in-memory state
    # ------------------------------------------------------------------

    change_registry = PrivacyChangeRegistry()
    case_registry = PrivacyGovernanceCaseRegistry()
    approval_registry = PrivacyApprovalRegistry()

    # ------------------------------------------------------------------
    # Optional infrastructure
    # ------------------------------------------------------------------

    resolved_approval_email_service = (
        _build_runtime_approval_email_service(
            approval_email_service=approval_email_service,
        )
    )

    # ------------------------------------------------------------------
    # Decision service
    # ------------------------------------------------------------------

    decision_service = PrivacyGovernanceDecisionService(
        approval_registry=approval_registry,
        change_registry=change_registry,
        case_registry=case_registry,
    )

    # ------------------------------------------------------------------
    # Governance gate
    # ------------------------------------------------------------------

    governance_gate = PrivacyGovernanceGate(
        registry=change_registry,
        validation_service=validation_service,
        approval_email_service=resolved_approval_email_service,
    )

    # ------------------------------------------------------------------
    # Case application service
    # ------------------------------------------------------------------

    case_service = PrivacyGovernanceCaseService(
        case_registry=case_registry,
        change_registry=change_registry,
        approval_registry=approval_registry,
        decision_service=decision_service,
    )

    # ------------------------------------------------------------------
    # End-to-end governance flow
    # ------------------------------------------------------------------

    flow_service = PrivacyGovernanceFlowService(
        change_registry=change_registry,
        governance_gate=governance_gate,
        case_service=case_service,
    )

    # ------------------------------------------------------------------
    # Dashboard/read model
    # ------------------------------------------------------------------

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


# ----------------------------------------------------------------------
# Runtime composition
# ----------------------------------------------------------------------

_runtime_composition: PrivacyGovernanceComposition | None = None


def get_privacy_governance_composition() -> PrivacyGovernanceComposition:
    """Return the process-wide Beta privacy governance composition.

    The same composition instance is reused during the application
    process so the Operations Center API and application integrations
    observe the same in-memory governance state.

    Email configuration is optional during composition creation.
    """

    global _runtime_composition

    if _runtime_composition is None:
        _runtime_composition = (
            create_privacy_governance_composition()
        )

    return _runtime_composition


def reset_privacy_governance_composition_for_tests() -> None:
    """Reset the process-wide composition.

    This function exists exclusively for test isolation.

    Production application code must not use this function to reset
    governance state.
    """

    global _runtime_composition

    _runtime_composition = None


__all__ = [
    "PrivacyGovernanceComposition",
    "create_privacy_governance_composition",
    "get_privacy_governance_composition",
    "reset_privacy_governance_composition_for_tests",
]