from __future__ import annotations

from backend.app.application.privacy.privacy_governance_case_url import (
    PrivacyGovernanceCaseURLBuilder,
)


def test_case_url_uses_configured_application_base_url():
    builder = PrivacyGovernanceCaseURLBuilder(
        app_base_url="http://127.0.0.1:5173/",
    )

    assert builder.build("CASE-E2E-001") == (
        "http://127.0.0.1:5173/"
        "privacy-governance/CASE-E2E-001"
    )
