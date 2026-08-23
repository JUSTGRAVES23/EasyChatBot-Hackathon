from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from backend.app.application.privacy.privacy_change_registry import (
    PrivacyChangeRegistry,
)
from backend.app.application.privacy.privacy_governance_case_service import (
    PrivacyGovernanceCaseService,
)
from backend.app.application.privacy.privacy_governance_case_registry import (
    PrivacyGovernanceCaseRegistry,
)
from backend.app.application.privacy.privacy_governance_decision_service import (
    PrivacyGovernanceDecisionService,
)
from backend.app.application.privacy.privacy_governance_flow_service import (
    PrivacyGovernanceFlowService,
)
from backend.app.application.privacy.privacy_governance_gate import (
    PrivacyGovernanceGate,
)
from backend.app.application.privacy.privacy_approval_registry import (
    PrivacyApprovalRegistry,
)
from backend.app.application.privacy.privacy_governance_case_url import (
    PrivacyGovernanceCaseURLBuilder,
)


class FakeReminderSender:
    def __init__(self) -> None:
        self.calls = []

    async def send(
        self,
        *,
        recipient: str,
        subject: str,
        body: str,
        html_body: str,
        attachments=None,
    ):
        self.calls.append(
            {
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "html_body": html_body,
                "attachments": attachments,
            }
        )

        return {
            "provider": "fake",
            "status": "accepted",
            "reference": "fake-message-id",
        }


def make_change() -> PrivacyChange:
    return PrivacyChange(
        change_id="PCR-E2E-001",
        title="Beta 1 Privacy Governance Email Test",
        description=(
            "Controlled end-to-end test of the "
            "privacy governance cascade."
        ),
        affected_processing_ids=[],
        affected_data_map_ids=[],
        risk=PrivacyChangeRisk.MEDIUM,
        status=PrivacyChangeStatus.DRAFT,
        dpo_required=True,
        grc_required=True,
        metadata={
            "test_type": "controlled_e2e",
        },
    )


def test_pcr_to_case_identity_is_preserved():
    """
    The Privacy Change Registry identity must be preserved when
    the governance case is created.

    Expected:

        PCR-E2E-001
            ↓
        CASE-E2E-001
    """

    change_registry = PrivacyChangeRegistry()
    case_registry = PrivacyGovernanceCaseRegistry()
    approval_registry = PrivacyApprovalRegistry()

    decision_service = PrivacyGovernanceDecisionService(
        case_registry=case_registry,
        change_registry=change_registry,
        approval_registry=approval_registry,
    )

    case_service = PrivacyGovernanceCaseService(
        case_registry=case_registry,
        change_registry=change_registry,
        approval_registry=approval_registry,
        decision_service=decision_service,
    )

    gate = PrivacyGovernanceGate(
        registry=change_registry,
    )

    flow = PrivacyGovernanceFlowService(
        change_registry=change_registry,
        governance_gate=gate,
        case_service=case_service,
    )

    result = flow.process_new_processing(
        make_change(),
        automated_validation_passed=True,
        case_id="CASE-E2E-001",
        trigger_source="Controlled E2E Test",
    )

    assert result.change.change_id == (
        "PCR-E2E-001"
    )

    assert result.case.case_id == (
        "CASE-E2E-001"
    )

    assert result.case.change_id == (
        "PCR-E2E-001"
    )

    assert result.case.validation_status == (
        "PASS"
    )

    assert result.case.governance_status == (
        "PENDING_DPO_GRC"
    )


def test_case_url_builder_uses_authoritative_case_id():
    """
    The frontend URL must be derived from the authoritative
    governance CASE ID, never reconstructed from the PCR ID.
    """

    builder = PrivacyGovernanceCaseURLBuilder(
        app_base_url="http://127.0.0.1:5173",
    )

    url = builder.build(
        "CASE-E2E-001"
    )

    assert url == (
        "http://127.0.0.1:5173/"
        "privacy-governance/CASE-E2E-001"
    )


@pytest.mark.asyncio
async def test_privacy_reminder_preserves_case_and_change_identity():
    """
    The reminder must preserve the complete audit cascade:

        PCR-E2E-001
             ↓
        CASE-E2E-001
             ↓
        Reminder
             ↓
        REVIEW THIS CASE
             ↓
        /privacy-governance/CASE-E2E-001
    """

    reminder_sender = FakeReminderSender()

    builder = PrivacyGovernanceCaseURLBuilder(
        app_base_url="http://127.0.0.1:5173",
    )

    from backend.app.application.privacy.email.privacy_governance_reminder_email_service import (
        PrivacyGovernanceReminderEmailService,
    )

    logo_path = Path(
        "backend/app/application/privacy/email/assets/"
        "easychatbot_logo.png"
    )

    service = PrivacyGovernanceReminderEmailService(
        sender=reminder_sender,
        recipient="reviewer@example.test",
        case_url_builder=builder,
        logo_path=logo_path,
    )

    case = type(
        "Case",
        (),
        {
            "case_id": "CASE-E2E-001",
            "change_id": "PCR-E2E-001",
            "title": "Beta 1 Privacy Governance Email Test",
            "summary": (
                "Controlled end-to-end test of the "
                "privacy governance cascade."
            ),
            "risk": "medium",
            "validation_status": "PASS",
            "governance_status": "PENDING_DPO_GRC",
        },
    )()

    result = await service.send_governance_reminder(
        case=case,
    )

    # --------------------------------------------------------
    # Authoritative identity
    #
    # The reminder service consumes the authoritative CASE
    # object. Its response does not need to duplicate these
    # identity fields.
    # --------------------------------------------------------

    assert case.change_id == (
        "PCR-E2E-001"
    )

    assert case.case_id == (
        "CASE-E2E-001"
    )

    # --------------------------------------------------------
    # Controlled destination
    #
    # The URL must always be derived from CASE-E2E-001.
    # --------------------------------------------------------

    expected_url = (
        "http://127.0.0.1:5173/"
        "privacy-governance/CASE-E2E-001"
    )

    assert result["case_url"] == expected_url

    # --------------------------------------------------------
    # Delivery
    # --------------------------------------------------------

    assert result["status"] == (
        "accepted"
    )

    assert result["reference"] == (
        "fake-message-id"
    )

    assert len(reminder_sender.calls) == 1

    email = reminder_sender.calls[0]

    # --------------------------------------------------------
    # Subject identity
    # --------------------------------------------------------

    assert (
        "CASE-E2E-001"
        in email["subject"]
    )

    # --------------------------------------------------------
    # Plain-text identity
    # --------------------------------------------------------

    assert (
        "PCR-E2E-001"
        in email["body"]
    )

    assert (
        "CASE-E2E-001"
        in email["body"]
    )

    assert expected_url in email["body"]

    # --------------------------------------------------------
    # HTML identity
    # --------------------------------------------------------

    assert (
        "PCR-E2E-001"
        in email["html_body"]
    )

    assert (
        "CASE-E2E-001"
        in email["html_body"]
    )

    assert (
        "REVIEW THIS CASE"
        in email["html_body"]
    )

    assert expected_url in email["html_body"]

    # --------------------------------------------------------
    # Inline logo contract
    # --------------------------------------------------------

    attachments = email["attachments"]

    assert isinstance(
        attachments,
        list,
    )

    assert len(attachments) == 1

    attachment = attachments[0]

    assert attachment["filename"] == (
        "easychatbot_logo.png"
    )

    assert attachment["content_id"] == (
        "easychatbot-governance-logo"
    )

    assert attachment["inline"] is True

    assert attachment["path"] == str(
        logo_path
    )