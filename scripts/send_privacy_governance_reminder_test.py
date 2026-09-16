from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import dotenv_values

# Make repository imports work when this file is executed directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ENV_FILE = REPO_ROOT / ".env"
_LOCAL_ENV = (
    dict(dotenv_values(ENV_FILE))
    if ENV_FILE.exists()
    else {}
)


def get_config(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None:
        return value
    value = _LOCAL_ENV.get(name)
    if value is not None:
        return str(value)
    return default


from app.application.privacy.email.privacy_governance_reminder_email_service import (
    PrivacyGovernanceReminderEmailService,
)
from app.application.privacy.privacy_governance_case_url import (
    PrivacyGovernanceCaseURLBuilder,
)
from app.infrastructure.privacy.privacy_governance_reminder_email_sender import (
    ResendGovernanceReminderEmailSender,
)
from cybersecurity.email.email_configuration import EMAIL_RECIPIENT


BACKEND_BASE_URL = get_config(
    "NEXT_PUBLIC_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

FRONTEND_BASE_URL = get_config(
    "PRIVACY_GOVERNANCE_APP_BASE_URL",
    "http://127.0.0.1:5173",
).rstrip("/")

CASE_ID = get_config(
    "PRIVACY_E2E_CASE_ID",
    "CASE-E2E-003",
)

BACKEND_CASE_URL = (
    f"{BACKEND_BASE_URL}/api/privacy/governance/cases/{CASE_ID}"
)

LOGO_PATH = (
    REPO_ROOT
    / "backend"
    / "app"
    / "application"
    / "privacy"
    / "email"
    / "assets"
    / "easychatbot_logo.png"
)

SEND_EMAIL = (
    get_config(
        "PRIVACY_E2E_SEND_EMAIL",
        "false",
    ).strip().lower()
    == "true"
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

    try:
        with urlopen(request, timeout=10) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"Case API returned HTTP {response.status}."
                )

            payload = json.loads(
                response.read().decode("utf-8")
            )

    except HTTPError as exc:
        raise RuntimeError(
            f"Case API returned HTTP {exc.code}: {BACKEND_CASE_URL}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"Could not connect to the FastAPI backend: {BACKEND_CASE_URL}"
        ) from exc

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
    print("EASYCHATBOT PRIVACY GOVERNANCE REMINDER E2E TEST")
    print("=" * 70)

    print()
    print("Repository:")
    print(REPO_ROOT)

    print()
    print("Backend:")
    print(BACKEND_BASE_URL)

    print()
    print("Frontend:")
    print(FRONTEND_BASE_URL)

    print()
    print("Case:")
    print(CASE_ID)

    print()
    print("PRIVACY_E2E_SEND_EMAIL:")
    print(SEND_EMAIL)

    if not EMAIL_RECIPIENT.strip():
        raise RuntimeError(
            "No email recipient is configured."
        )

    if not LOGO_PATH.exists():
        raise FileNotFoundError(
            f"Governance logo not found: {LOGO_PATH}"
        )

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
    print("Expected REVIEW THIS CASE destination:")
    print(expected_case_url)

    if "awstrack.me" in expected_case_url.lower():
        raise RuntimeError(
            "Expected case URL must be the application URL, "
            "not an AWS tracking URL."
        )

    if not expected_case_url.startswith(
        f"{FRONTEND_BASE_URL}/privacy-governance/"
    ):
        raise RuntimeError(
            "Generated case URL is outside the expected "
            "Privacy Governance route."
        )

    print()
    print("URL preflight:")
    print("PASS - direct application URL generated.")
    print("PASS - no awstrack.me wrapper in application URL.")

    if not SEND_EMAIL:
        print()
        print("EMAIL NOT SENT")
        print("-" * 70)
        print(
            "Set PRIVACY_E2E_SEND_EMAIL=true in the repository .env "
            "to perform the real Resend delivery test."
        )
        print()
        print("Expected destination:")
        print(expected_case_url)
        print("=" * 70)
        return

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

    if returned_url and "awstrack.me" in returned_url.lower():
        raise RuntimeError(
            "The returned case URL is unexpectedly wrapped by AWS tracking."
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
    print("MANUAL EMAIL TEST")
    print("1. Open the NEW email.")
    print("2. Click REVIEW THIS CASE.")
    print("3. Confirm the browser opens:")
    print(f"   {expected_case_url}")
    print("4. Confirm the URL does NOT remain on awstrack.me.")
    print("5. Confirm the case page loads.")
    print("6. Confirm the case data matches CASE ID:", case.case_id)
    print()
    print("Expected destination:")
    print(expected_case_url)
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
