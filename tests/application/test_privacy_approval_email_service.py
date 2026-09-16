from app.application.privacy.privacy_approval_email_service import (
    PrivacyApprovalEmailService,
)
from app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
)


class FakeSender:
    def __init__(self):
        self.requests = []

    def send(self, request):
        self.requests.append(request)


def make_change():
    return PrivacyChange(
        change_id="PCR-EMAIL-001",
        title="Add new learner analytics",
        description="Introduce a new privacy-impacting analytics flow.",
        risk=PrivacyChangeRisk.MEDIUM,
        dpo_required=True,
        grc_required=True,
    )


def test_email_escalation_requires_human_approval():
    sender = FakeSender()
    service = PrivacyApprovalEmailService(
        sender=sender,
        approval_recipient="configured-reviewer@example.test",
    )

    request = service.escalate(
        make_change(),
        validation_passed=True,
    )

    assert request.recipient == "configured-reviewer@example.test"
    assert request.change_id == "PCR-EMAIL-001"
    assert request.requires_dpo_approval is True
    assert request.requires_grc_approval is True
    assert len(sender.requests) == 1
    assert "does not itself constitute approval" in request.body


def test_email_escalation_refuses_failed_validation():
    sender = FakeSender()
    service = PrivacyApprovalEmailService(
        sender=sender,
        approval_recipient="configured-reviewer@example.test",
    )

    try:
        service.escalate(make_change(), validation_passed=False)
    except ValueError as exc:
        assert "validation" in str(exc).lower()
    else:
        raise AssertionError("Escalation was allowed despite failed validation")

    assert sender.requests == []

