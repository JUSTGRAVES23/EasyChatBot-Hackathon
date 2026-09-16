from __future__ import annotations

import pytest

from app.application.privacy.privacy_approval_email_service import (
    PrivacyApprovalEmailService,
)
from app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from app.application.privacy.privacy_change_registry import (
    PrivacyChangeRegistry,
)
from app.application.privacy.privacy_governance_gate import (
    PrivacyGovernanceGate,
)


class FakeApprovalEmailSender:
    """Deterministic synchronous test double; no real email is sent."""

    def __init__(self) -> None:
        self.requests = []

    def send(self, request) -> None:
        """Record the email request without sending a real email."""
        self.requests.append(request)


class FakeValidationResult:
    def __init__(self, status: str) -> None:
        self.status = status
        self.checks = 16
        self.passed = 16 if status == "PASS" else 15
        self.failures = () if status == "PASS" else ("privacy gap",)


class FakePrivacyValidationService:
    def __init__(self, status: str) -> None:
        self.status = status
        self.calls = 0

    def validate(self) -> FakeValidationResult:
        self.calls += 1
        return FakeValidationResult(self.status)


def make_change(
    *,
    dpo_required: bool = True,
    grc_required: bool = True,
) -> PrivacyChange:
    return PrivacyChange(
        change_id="PCR-TEST-001",
        title="Test privacy-impacting change",
        description="Controlled governance gate test.",
        risk=PrivacyChangeRisk.MEDIUM,
        dpo_required=dpo_required,
        grc_required=grc_required,
    )


def make_gate(
    *,
    validation_status: str,
    sender: FakeApprovalEmailSender,
):
    registry = PrivacyChangeRegistry()

    validation = FakePrivacyValidationService(
        validation_status
    )

    email_service = PrivacyApprovalEmailService(
        sender=sender,
        approval_recipient="davdbarbero1999@gmail.com",
    )

    gate = PrivacyGovernanceGate(
        registry=registry,
        validation_service=validation,
        approval_email_service=email_service,
    )

    return gate, registry, validation


@pytest.mark.asyncio
async def test_pass_dpo_grc_required_sends_email_and_remains_pending():
    sender = FakeApprovalEmailSender()

    gate, registry, validation = make_gate(
        validation_status="PASS",
        sender=sender,
    )

    result = await gate.route_and_escalate(
        make_change(
            dpo_required=True,
            grc_required=True,
        )
    )

    assert result.status == PrivacyChangeStatus.PENDING_DPO_GRC

    assert len(sender.requests) == 1

    request = sender.requests[0]

    assert request.recipient == "davdbarbero1999@gmail.com"
    assert request.requires_dpo_approval is True
    assert request.requires_grc_approval is True

    # Email delivery must never equal governance approval.
    assert result.status != PrivacyChangeStatus.APPROVED

    assert gate.can_proceed(
        "PCR-TEST-001"
    ) is False

    assert validation.calls == 1


@pytest.mark.asyncio
async def test_fail_dpo_grc_required_sends_no_email_and_blocks():
    sender = FakeApprovalEmailSender()

    gate, registry, validation = make_gate(
        validation_status="FAIL",
        sender=sender,
    )

    result = await gate.route_and_escalate(
        make_change(
            dpo_required=True,
            grc_required=True,
        )
    )

    assert result.status == PrivacyChangeStatus.BLOCKED

    assert sender.requests == []

    assert gate.can_proceed(
        "PCR-TEST-001"
    ) is False

    assert validation.calls == 1


@pytest.mark.asyncio
async def test_pass_without_dpo_grc_requirement_sends_no_email_and_approves():
    sender = FakeApprovalEmailSender()

    gate, registry, validation = make_gate(
        validation_status="PASS",
        sender=sender,
    )

    result = await gate.route_and_escalate(
        make_change(
            dpo_required=False,
            grc_required=False,
        )
    )

    assert result.status == PrivacyChangeStatus.APPROVED

    assert sender.requests == []

    assert gate.can_proceed(
        "PCR-TEST-001"
    ) is True

    assert validation.calls == 1


@pytest.mark.asyncio
async def test_email_sent_does_not_mean_approved():
    sender = FakeApprovalEmailSender()

    gate, registry, validation = make_gate(
        validation_status="PASS",
        sender=sender,
    )

    result = await gate.route_and_escalate(
        make_change(
            dpo_required=True,
            grc_required=True,
        )
    )

    assert len(sender.requests) == 1

    assert result.status == PrivacyChangeStatus.PENDING_DPO_GRC

    assert gate.can_proceed(
        "PCR-TEST-001"
    ) is False
