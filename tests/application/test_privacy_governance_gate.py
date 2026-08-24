from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from backend.app.application.privacy.privacy_approval_email_service import (
    PrivacyApprovalEmailService,
)
from backend.app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from backend.app.application.privacy.privacy_change_registry import (
    PrivacyChangeRegistry,
)
from backend.app.application.privacy.privacy_governance_gate import (
    PrivacyGovernanceGate,
)


@dataclass(frozen=True)
class ValidationResult:
    status: str


class FakeValidationService:
    """Deterministic validation service for gate tests."""

    def __init__(self, status: str = "PASS") -> None:
        self.status = status
        self.calls = 0

    def validate(self) -> ValidationResult:
        self.calls += 1
        return ValidationResult(
            status=self.status,
        )


class FakeApprovalEmailSender:
    """Application-boundary fake for approval email delivery."""

    def __init__(self) -> None:
        self.requests = []

    async def send(self, request):
        self.requests.append(request)

        return {
            "status": "accepted",
            "message_id": "MSG-APPROVAL-001",
            "reference": "MSG-APPROVAL-001",
            "case_id": request.case_id,
            "change_id": request.change_id,
        }


def make_change(
    *,
    change_id: str = "PCR-GATE-001",
    dpo_required: bool = True,
    grc_required: bool = True,
) -> PrivacyChange:
    return PrivacyChange(
        change_id=change_id,
        title="Controlled privacy change",
        description="Privacy governance gate test.",
        risk=PrivacyChangeRisk.MEDIUM,
        status=PrivacyChangeStatus.PENDING_DPO_GRC,
        dpo_required=dpo_required,
        grc_required=grc_required,
    )


def make_registry(
    change: PrivacyChange,
) -> PrivacyChangeRegistry:
    registry = PrivacyChangeRegistry()
    registry.register(change)
    return registry


def make_gate(
    *,
    change: PrivacyChange | None = None,
    validation_status: str = "PASS",
):
    if change is None:
        change = make_change()

    registry = make_registry(change)

    validation_service = FakeValidationService(
        status=validation_status,
    )

    sender = FakeApprovalEmailSender()

    approval_email_service = PrivacyApprovalEmailService(
        sender=sender,
        approval_recipient="dpo@example.test",
    )

    gate = PrivacyGovernanceGate(
        registry=registry,
        validation_service=validation_service,
        approval_email_service=approval_email_service,
    )

    return (
        gate,
        registry,
        validation_service,
        sender,
    )


def test_route_blocks_when_validation_fails():
    change = make_change()

    gate, registry, validation, sender = make_gate(
        change=change,
        validation_status="FAIL",
    )

    result = gate.route_and_escalate.__wrapped__ if False else None

    # Synchronous route() uses the configured validation service
    # as the authoritative validation source.
    result = gate.route(change)

    assert result.status == PrivacyChangeStatus.BLOCKED

    stored = registry.get("PCR-GATE-001")

    assert stored.status == PrivacyChangeStatus.BLOCKED

    assert validation.calls == 1

    # route() must not send an email.
    assert sender.requests == []


@pytest.mark.asyncio
async def test_route_and_escalate_blocks_when_validation_fails():
    change = make_change()

    gate, registry, validation, sender = make_gate(
        change=change,
        validation_status="FAIL",
    )

    result = await gate.route_and_escalate(
        change,
    )

    assert result.status == PrivacyChangeStatus.BLOCKED

    stored = registry.get("PCR-GATE-001")

    assert stored.status == PrivacyChangeStatus.BLOCKED

    assert validation.calls == 1

    # Failed validation must never trigger governance email.
    assert sender.requests == []


@pytest.mark.asyncio
async def test_route_and_escalate_requires_human_governance():
    change = make_change(
        dpo_required=True,
        grc_required=True,
    )

    gate, registry, validation, sender = make_gate(
        change=change,
        validation_status="PASS",
    )

    result = await gate.route_and_escalate(
        change,
    )

    assert result.status == PrivacyChangeStatus.PENDING_DPO_GRC

    stored = registry.get("PCR-GATE-001")

    assert stored.status == PrivacyChangeStatus.PENDING_DPO_GRC

    assert validation.calls == 1

    assert len(sender.requests) == 1

    request = sender.requests[0]

    assert request.change_id == "PCR-GATE-001"
    assert request.recipient == "dpo@example.test"
    assert request.requires_dpo_approval is True
    assert request.requires_grc_approval is True


@pytest.mark.asyncio
async def test_route_and_escalate_does_not_treat_email_delivery_as_approval():
    change = make_change()

    gate, registry, _, sender = make_gate(
        change=change,
        validation_status="PASS",
    )

    result = await gate.route_and_escalate(
        change,
    )

    assert result.status == PrivacyChangeStatus.PENDING_DPO_GRC

    stored = registry.get("PCR-GATE-001")

    assert stored.status == PrivacyChangeStatus.PENDING_DPO_GRC

    assert len(sender.requests) == 1


@pytest.mark.asyncio
async def test_route_and_escalate_returns_pending_change_after_email():
    change = make_change()

    gate, _, _, sender = make_gate(
        change=change,
        validation_status="PASS",
    )

    result = await gate.route_and_escalate(
        change,
    )

    assert result.change_id == "PCR-GATE-001"
    assert result.status == PrivacyChangeStatus.PENDING_DPO_GRC

    assert len(sender.requests) == 1


def test_route_approves_when_no_governance_review_is_required():
    change = make_change(
        dpo_required=False,
        grc_required=False,
    )

    gate, registry, validation, sender = make_gate(
        change=change,
        validation_status="PASS",
    )

    result = gate.route(change)

    assert result.status == PrivacyChangeStatus.APPROVED

    stored = registry.get("PCR-GATE-001")

    assert stored.status == PrivacyChangeStatus.APPROVED

    assert validation.calls == 1

    # Synchronous route() never sends an email.
    assert sender.requests == []


@pytest.mark.asyncio
async def test_route_and_escalate_approves_without_email_when_governance_not_required():
    change = make_change(
        dpo_required=False,
        grc_required=False,
    )

    gate, registry, validation, sender = make_gate(
        change=change,
        validation_status="PASS",
    )

    result = await gate.route_and_escalate(
        change,
    )

    assert result.status == PrivacyChangeStatus.APPROVED

    stored = registry.get("PCR-GATE-001")

    assert stored.status == PrivacyChangeStatus.APPROVED

    assert validation.calls == 1

    assert sender.requests == []


def test_route_requires_explicit_validation_without_validation_service():
    change = make_change()

    registry = make_registry(change)

    gate = PrivacyGovernanceGate(
        registry=registry,
    )

    with pytest.raises(
        ValueError,
        match="automated_validation_passed is required",
    ):
        gate.route(change)


def test_route_uses_explicit_validation_without_validation_service():
    change = make_change()

    registry = make_registry(change)

    gate = PrivacyGovernanceGate(
        registry=registry,
    )

    result = gate.route(
        change,
        automated_validation_passed=True,
    )

    assert result.status == PrivacyChangeStatus.PENDING_DPO_GRC


@pytest.mark.asyncio
async def test_route_and_escalate_requires_validation_service():
    change = make_change()

    registry = make_registry(change)

    sender = FakeApprovalEmailSender()

    approval_email_service = PrivacyApprovalEmailService(
        sender=sender,
        approval_recipient="dpo@example.test",
    )

    gate = PrivacyGovernanceGate(
        registry=registry,
        approval_email_service=approval_email_service,
    )

    with pytest.raises(
        RuntimeError,
        match="PrivacyValidationService is required",
    ):
        await gate.route_and_escalate(change)


@pytest.mark.asyncio
async def test_route_and_escalate_requires_approval_email_service():
    change = make_change()

    registry = make_registry(change)

    validation_service = FakeValidationService(
        status="PASS",
    )

    gate = PrivacyGovernanceGate(
        registry=registry,
        validation_service=validation_service,
    )

    with pytest.raises(
        RuntimeError,
        match="PrivacyApprovalEmailService is required",
    ):
        await gate.route_and_escalate(change)


def test_can_proceed_is_false_for_pending_change():
    change = make_change()

    gate, _, _, _ = make_gate(
        change=change,
    )

    assert gate.can_proceed(
        "PCR-GATE-001",
    ) is False


def test_can_proceed_is_true_for_approved_change():
    change = make_change(
        dpo_required=False,
        grc_required=False,
    )

    gate, _, _, _ = make_gate(
        change=change,
        validation_status="PASS",
    )

    gate.route(change)

    assert gate.can_proceed(
        "PCR-GATE-001",
    ) is True


def test_can_proceed_is_false_for_blocked_change():
    change = make_change()

    gate, _, _, _ = make_gate(
        change=change,
        validation_status="FAIL",
    )

    gate.route(change)

    assert gate.can_proceed(
        "PCR-GATE-001",
    ) is False


def test_can_proceed_requires_change_id():
    change = make_change()

    gate, _, _, _ = make_gate(
        change=change,
    )

    with pytest.raises(
        ValueError,
        match="change_id is required",
    ):
        gate.can_proceed("")


def test_route_rejects_none_change():
    change = make_change()

    gate, _, _, _ = make_gate(
        change=change,
    )

    with pytest.raises(
        ValueError,
        match="change cannot be None",
    ):
        gate.route(None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_route_and_escalate_rejects_none_change():
    change = make_change()

    gate, _, _, _ = make_gate(
        change=change,
    )

    with pytest.raises(
        ValueError,
        match="change cannot be None",
    ):
        await gate.route_and_escalate(
            None,  # type: ignore[arg-type]
        )