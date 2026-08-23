from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from urllib.request import Request, urlopen

from backend.app.application.privacy.email.privacy_governance_reminder_email_service import (
    PrivacyGovernanceReminderEmailService,
)
from backend.app.application.privacy.privacy_governance_case_url import (
    PrivacyGovernanceCaseURLBuilder,
)
from backend.app.infrastructure.privacy.privacy_governance_reminder_email_sender import (
    ResendGovernanceReminderEmailSender,
)
from backend.cybersecurity.email.email_configuration import (
    EMAIL_RECIPIENT,
)


BACKEND_CASE_URL = (
    "http://127.0.0.1:8000"
    "/api/privacy/governance/cases/CASE-E2E-003"
)

FRONTEND_BASE_URL = "http://127.0.0.1:5173"

LOGO_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "app"
    / "application"
    / "privacy"
    / "email"
    / "assets"
    / "easychatbot_logo.png"
)

SUCCESS_STATUSES = {
    "accepted",
    "sent",
    "success",
}


def load_case() -> SimpleNamespace:
    """Load the authoritative case from the running FastAPI application."""

    request = Request(
        BACKEND_CASE_URL,
        method="GET",
    )

    with urlopen(request, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(
                f"Case API returned HTTP {response.status}."
            )

        payload = json.loads(
            response.read().decode("utf-8")
        )

    return SimpleNamespace(
        case_id=payload["case_id"],
        change_id=payload.get("change_id"),
        title=payload.get(
            "title",
            "Privacy governance case",
        ),
        risk=payload.get(
            "risk",
            "N/A",
        ),
        validation_status=payload.get(
            "validation_status",
            "N/A",
        ),
        governance_status=payload.get(
            "governance_status",
            "PENDING_DPO_GRC",
        ),
    )


async def main() -> None:
    print("=" * 70)
    print("EASYCHATBOT PRIVACY GOVERNANCE REAL EMAIL TEST")
    print("=" * 70)

    if not EMAIL_RECIPIENT.strip():
        raise RuntimeError(
            "No email recipient is configured."
        )

    if not LOGO_PATH.exists():
        raise FileNotFoundError(
            f"Governance logo not found: {LOGO_PATH}"
        )

    print()
    print("Recipient:")
    print(EMAIL_RECIPIENT)

    print()
    print("Loading authoritative case from:")
    print(BACKEND_CASE_URL)

    case = load_case()

    print()
    print("Case:")
    print(case.case_id)

    print("Change:")
    print(case.change_id)

    print("Governance status:")
    print(case.governance_status)

    case_url_builder = PrivacyGovernanceCaseURLBuilder(
        app_base_url=FRONTEND_BASE_URL,
    )

    expected_case_url = case_url_builder.build(
        case.case_id
    )

    print()
    print("Generated case URL:")
    print(expected_case_url)

    sender = ResendGovernanceReminderEmailSender()

    service = PrivacyGovernanceReminderEmailService(
        sender=sender,
        recipient=EMAIL_RECIPIENT,
        case_url_builder=case_url_builder,
        logo_path=LOGO_PATH,
    )

    print()
    print("Sending real reminder email through:")
    print("PrivacyGovernanceReminderEmailService")
    print("        ->")
    print("ResendGovernanceReminderEmailSender")
    print("        ->")
    print("EmailProviderManager")
    print("        ->")
    print("Resend")

    result = await service.send_governance_reminder(
        case=case,
    )

    print()
    print("=" * 70)
    print("EMAIL DELIVERY RESULT")
    print("=" * 70)

    print(json.dumps(result, indent=2))

    provider_status = result.get("status")

    if provider_status not in SUCCESS_STATUSES:
        raise RuntimeError(
            "Reminder email was not accepted by the email provider: "
            f"{result}"
        )

    returned_url = result.get("case_url")

    if returned_url != expected_case_url:
        raise RuntimeError(
            "Generated case URL mismatch: "
            f"expected={expected_case_url!r}, "
            f"returned={returned_url!r}"
        )

    print()
    print("SUCCESS")
    print("-" * 70)
    print("Case ID:", case.case_id)
    print("Email status:", provider_status)
    print("Email reference:", result.get("reference"))
    print("Case URL:", returned_url)
    print()
    print("Provider accepted the email for delivery.")
    print()
    print("Open the email and click:")
    print("REVIEW THIS CASE")
    print()
    print("Expected destination:")
    print(expected_case_url)
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
