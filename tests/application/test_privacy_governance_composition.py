from __future__ import annotations

from unittest.mock import Mock

from app.application.privacy.privacy_approval_email_service import (
    PrivacyApprovalEmailService,
)
from app.application.privacy.privacy_governance_composition import (
    PrivacyGovernanceComposition,
    create_privacy_governance_composition,
    reset_privacy_governance_composition_for_tests,
)
from app.application.privacy.privacy_governance_gate import (
    PrivacyGovernanceGate,
)


def test_create_composition_returns_coherent_runtime_components() -> None:
    composition = create_privacy_governance_composition()

    assert isinstance(
        composition,
        PrivacyGovernanceComposition,
    )

    assert composition.change_registry is not None
    assert composition.case_registry is not None
    assert composition.approval_registry is not None
    assert composition.decision_service is not None
    assert composition.governance_gate is not None
    assert composition.case_service is not None
    assert composition.flow_service is not None
    assert composition.dashboard_service is not None


def test_composition_shares_authoritative_registries() -> None:
    composition = create_privacy_governance_composition()

    assert (
        composition.decision_service._approvals
        is composition.approval_registry
    )

    assert (
        composition.decision_service._changes
        is composition.change_registry
    )

    assert (
        composition.decision_service._cases
        is composition.case_registry
    )

    assert (
        composition.case_service.case_registry
        is composition.case_registry
    )

    assert (
        composition.case_service.change_registry
        is composition.change_registry
    )

    assert (
        composition.case_service.approval_registry
        is composition.approval_registry
    )


def test_explicit_approval_email_service_is_injected() -> None:
    sender = Mock()

    approval_email_service = PrivacyApprovalEmailService(
        sender=sender,
        approval_recipient="dpo@example.test",
    )

    composition = create_privacy_governance_composition(
        approval_email_service=approval_email_service,
    )

    gate = composition.governance_gate

    assert isinstance(
        gate,
        PrivacyGovernanceGate,
    )

    assert gate._approval_email is approval_email_service


def test_explicit_validation_service_is_injected() -> None:
    validation_service = Mock()

    composition = create_privacy_governance_composition(
        validation_service=validation_service,
    )

    assert (
        composition.governance_gate._validation
        is validation_service
    )


def test_runtime_composition_is_singleton() -> None:
    reset_privacy_governance_composition_for_tests()

    from app.application.privacy.privacy_governance_composition import (
        get_privacy_governance_composition,
    )

    first = get_privacy_governance_composition()
    second = get_privacy_governance_composition()

    assert first is second

    reset_privacy_governance_composition_for_tests()


def test_runtime_composition_can_be_reset_for_tests() -> None:
    reset_privacy_governance_composition_for_tests()

    from app.application.privacy.privacy_governance_composition import (
        get_privacy_governance_composition,
    )

    first = get_privacy_governance_composition()

    reset_privacy_governance_composition_for_tests()

    second = get_privacy_governance_composition()

    assert first is not second

    reset_privacy_governance_composition_for_tests()


def test_composition_does_not_create_duplicate_registries() -> None:
    composition = create_privacy_governance_composition()

    assert (
        composition.case_service.case_registry
        is composition.case_registry
    )

    assert (
        composition.case_service.change_registry
        is composition.change_registry
    )

    assert (
        composition.case_service.approval_registry
        is composition.approval_registry
    )

    assert (
        composition.decision_service._cases
        is composition.case_registry
    )

    assert (
        composition.decision_service._changes
        is composition.change_registry
    )

    assert (
        composition.decision_service._approvals
        is composition.approval_registry
    )
