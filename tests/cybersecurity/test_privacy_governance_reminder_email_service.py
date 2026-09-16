from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from app.application.privacy.email.privacy_governance_reminder_email_service import (
    PrivacyGovernanceReminderEmailService,
)
from app.application.privacy.privacy_governance_case_url import (
    PrivacyGovernanceCaseURLBuilder,
)


@dataclass(frozen=True)
class Case:
    case_id: str = "CASE-E2E-001"
    change_id: str = "PCR-E2E-001"
    title: str = "New learner data processing"
    risk: str = "MEDIUM"
    validation_status: str = "PASS"
    governance_status: str = "PENDING_DPO_GRC"


class FakeSender:
    def __init__(self):
        self.calls = []

    async def send(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "status": "sent",
            "message_id": "MSG-001",
        }


@pytest.mark.asyncio
async def test_reminder_is_concise_and_contains_case_link_and_logo(tmp_path: Path):
    logo = tmp_path / "easychatbot_logo.png"
    logo.write_bytes(b"logo")

    sender = FakeSender()
    service = PrivacyGovernanceReminderEmailService(
        sender=sender,
        recipient="dpo@example.test",
        case_url_builder=PrivacyGovernanceCaseURLBuilder(
            app_base_url="http://127.0.0.1:5173",
        ),
        logo_path=logo,
    )

    result = await service.send_governance_reminder(case=Case())

    assert result["status"] == "sent"
    assert result["reference"] == "MSG-001"

    call = sender.calls[0]
    assert call["subject"] == (
        "[EasyChatBot Privacy Governance] "
        "Reminder â€” Decision Required for CASE-E2E-001"
    )
    assert "REVIEW THIS CASE" in call["html_body"]
    assert (
        "http://127.0.0.1:5173/privacy-governance/CASE-E2E-001"
        in call["html_body"]
    )
    assert "easychatbot-governance-logo" in call["html_body"]
    assert call["attachments"][0]["content_id"] == (
        "easychatbot-governance-logo"
    )
    assert call["attachments"][0]["inline"] is True

    # Reminder must remain shorter in scope than the initial approval email:
    assert "Possible decisions:" not in call["html_body"]
    assert "ACTION REQUIRED" not in call["html_body"]

