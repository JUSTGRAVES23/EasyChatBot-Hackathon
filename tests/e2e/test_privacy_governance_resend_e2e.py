from __future__ import annotations

import os

import pytest

from app.application.privacy.data_processing_map import (
    DataProcessingMap,
    DataProcessingMapEntry,
)
from app.application.privacy.dpia_screening import (
    DPIAScreening,
    DPIAScreeningRegistry,
)
from app.application.privacy.processing_activity import (
    ProcessingActivity,
)
from app.application.privacy.processing_registry import (
    ProcessingRegistry,
)
from app.application.privacy.processor_registry import (
    ProcessorRecord,
    ProcessorRegistry,
)
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
from app.application.privacy.privacy_validation_service import (
    PrivacyValidationService,
)
from app.application.privacy.retention_registry import (
    RetentionRegistry,
    RetentionRule,
)
from app.infrastructure.email.resend_approval_email_sender import (
    ResendApprovalEmailSender,
)


# ---------------------------------------------------------------------------
# REAL E2E TEST SAFETY SWITCH
# ---------------------------------------------------------------------------

E2E_ENABLED = (
    os.getenv(
        "PRIVACY_E2E_SEND_EMAIL",
        "",
    )
    .strip()
    .lower()
    == "true"
)


# ---------------------------------------------------------------------------
# Controlled E2E identifiers
# ---------------------------------------------------------------------------

PROCESSING_ID = "PROC-E2E-001"
DATA_MAP_ID = "MAP-E2E-001"
RETENTION_ID = "RET-E2E-001"
PROCESSOR_ID = "PROC-PROVIDER-E2E-001"
DPIA_SCREENING_ID = "DPIA-E2E-001"
CHANGE_ID = "PCR-E2E-001"


# ---------------------------------------------------------------------------
# Configuration validation
# ---------------------------------------------------------------------------


def _require_e2e_configuration() -> None:
    """
    Fail safely when the real Resend E2E test is explicitly enabled.

    The API key is never printed.
    """

    required = {
        "RESEND_API_KEY": os.getenv(
            "RESEND_API_KEY",
            "",
        ).strip(),
        "PRIVACY_APPROVAL_EMAIL_FROM": os.getenv(
            "PRIVACY_APPROVAL_EMAIL_FROM",
            "",
        ).strip(),
        "PRIVACY_APPROVAL_EMAIL_TO": os.getenv(
            "PRIVACY_APPROVAL_EMAIL_TO",
            "",
        ).strip(),
    }

    missing = [
        name
        for name, value in required.items()
        if not value
    ]

    if missing:
        pytest.fail(
            "Privacy Resend E2E test is enabled, but required "
            "configuration is missing: "
            f"{', '.join(missing)}"
        )


# ---------------------------------------------------------------------------
# Real PrivacyValidationService
# ---------------------------------------------------------------------------


def _build_validation_service() -> PrivacyValidationService:
    """
    Build the real deterministic PrivacyValidationService.

    This is intentionally not a fake validation service.

    The E2E test must prove that the actual privacy validation layer
    passes before an email can be sent.
    """

    processing_activity = ProcessingActivity(
        processing_id=PROCESSING_ID,
        name="Beta 1 Privacy Governance E2E Test",
        purpose=(
            "Controlled end-to-end validation of the "
            "EasyChatBot privacy governance workflow."
        ),
        data_categories=(
            "account identifier",
            "learning interaction data",
        ),
        data_subjects=(
            "registered learner",
        ),
        source=(
            "EasyChatBot application",
        ),
        destinations=(
            "EasyChatBot backend",
            "approved email recipient",
        ),
        legal_basis=(
            "Documented Beta 1 lawful basis recorded in the "
            "controlled privacy assessment."
        ),
        retention_id=RETENTION_ID,
        processor_ids=(
            PROCESSOR_ID,
        ),
        data_map_id=DATA_MAP_ID,
        dpia_screening_id=DPIA_SCREENING_ID,
        gdpr_references=(
            "GDPR Art. 5(1)(a)",
            "GDPR Art. 5(1)(b)",
            "GDPR Art. 6",
            "GDPR Art. 13/14",
            "GDPR Art. 28",
            "GDPR Art. 30",
            "GDPR Art. 35 where applicable",
        ),
        security_controls=(
            "access control",
            "least privilege",
            "audit logging",
            "encryption in transit",
        ),
        approval_status="APPROVED",
    )

    processing_registry = ProcessingRegistry(
        [
            processing_activity,
        ]
    )

    data_processing_map = DataProcessingMap(
        [
            DataProcessingMapEntry(
                map_id=DATA_MAP_ID,
                processing_id=PROCESSING_ID,
                source="EasyChatBot application",
                input_data=(
                    "account identifier",
                    "learning interaction data",
                ),
                runtime_processing=(
                    "privacy validation",
                    "governance routing",
                ),
                pseudonymisation=(
                    "Learner identifiers are minimised "
                    "and pseudonymised where applicable."
                ),
                persistence=(
                    "controlled governance registry",
                ),
                destinations=(
                    "EasyChatBot backend",
                    "approved email recipient",
                ),
                third_country_transfer=False,
                transfer_safeguard=None,
            ),
        ]
    )

    retention_registry = RetentionRegistry(
        [
            RetentionRule(
                retention_id=RETENTION_ID,
                data_domain="privacy governance",
                record_type="privacy change evidence",
                retention_period=(
                    "Beta 1 controlled retention period"
                ),
                trigger="governance record closure",
                deletion_action=(
                    "delete or securely dispose of the record "
                    "according to the approved retention policy"
                ),
                legal_policy_basis=(
                    "Controlled privacy/GRC retention policy."
                ),
            ),
        ]
    )

    processor_registry = ProcessorRegistry(
        [
            ProcessorRecord(
                processor_id=PROCESSOR_ID,
                provider_name="Resend",
                role="email delivery provider",
                processor_agreement_art28=(
                    "Contractual processor assessment required "
                    "and maintained in the processor registry."
                ),
                hosting_location=(
                    "Configured provider environment"
                ),
                third_country=False,
                safeguard_art46_47=None,
                dpo_status="REVIEWED",
                grc_status="REVIEWED",
                legal_status="REVIEWED",
            ),
        ]
    )

    dpia_registry = DPIAScreeningRegistry(
        [
            DPIAScreening(
                screening_id=DPIA_SCREENING_ID,
                processing_id=PROCESSING_ID,
                overall_risk="LOW",
                dpia_required="NO",
                dpo_assessment=(
                    "Screened for Beta 1 scope."
                ),
                grc_assessment=(
                    "Screened for Beta 1 governance scope."
                ),
                status="COMPLETED",
            ),
        ]
    )

    return PrivacyValidationService(
        processing_registry=processing_registry,
        data_processing_map=data_processing_map,
        retention_registry=retention_registry,
        processor_registry=processor_registry,
        dpia_registry=dpia_registry,
    )


# ---------------------------------------------------------------------------
# Controlled Privacy Change
# ---------------------------------------------------------------------------


def _build_change() -> PrivacyChange:
    """
    Create the controlled PCR-E2E-001 governance change.
    """

    return PrivacyChange(
        change_id=CHANGE_ID,
        title="Beta 1 Privacy Governance Email Test",
        description=(
            "Controlled end-to-end test proving that a privacy "
            "change which passes automated privacy validation "
            "and requires DPO/GRC review generates an approval "
            "escalation through Resend."
        ),
        affected_processing_ids=[
            PROCESSING_ID,
        ],
        affected_data_map_ids=[
            DATA_MAP_ID,
        ],
        risk=PrivacyChangeRisk.MEDIUM,
        status=PrivacyChangeStatus.DRAFT,
        dpo_required=True,
        grc_required=True,
        metadata={
            "test_type": "controlled_e2e",
            "test_id": CHANGE_ID,
            "purpose": (
                "Verify Resend delivery and governance routing."
            ),
        },
    )


# ---------------------------------------------------------------------------
# Real Resend E2E test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.skipif(
    not E2E_ENABLED,
    reason=(
        "Real Resend delivery disabled. Set "
        "PRIVACY_E2E_SEND_EMAIL=true to explicitly run "
        "this test."
    ),
)
async def test_privacy_governance_resend_e2e():
    """
    Controlled real Resend E2E test.

    The expected flow is:

        PrivacyValidationService
                    |
                  PASS
                    |
                    v
        PrivacyGovernanceGate
                    |
                    v
           PENDING_DPO_GRC
                    |
                    v
        PrivacyApprovalEmailService
                    |
                    v
        ResendApprovalEmailSender
                    |
                    v
                 Resend
                    |
                    v
          DPO/GRC mailbox

    Critical governance invariant:

        Email sent != governance approval.
    """

    # ------------------------------------------------------------------
    # 0. Verify that the explicit E2E configuration exists.
    # ------------------------------------------------------------------

    _require_e2e_configuration()

    # ------------------------------------------------------------------
    # 1. Build the REAL PrivacyValidationService.
    # ------------------------------------------------------------------

    validation_service = _build_validation_service()

    # ------------------------------------------------------------------
    # 2. Execute REAL automated privacy validation.
    # ------------------------------------------------------------------

    validation = validation_service.validate()

    assert validation.status == "PASS", (
        "The controlled E2E processing activity must pass "
        "PrivacyValidationService before any email can be sent. "
        f"Failures: {validation.failures}"
    )

    assert validation.failures == ()

    assert validation.checks > 0

    assert (
        validation.passed
        == validation.checks
    )

    # ------------------------------------------------------------------
    # 3. Build the REAL Resend infrastructure adapter.
    # ------------------------------------------------------------------

    resend_sender = ResendApprovalEmailSender(
        api_key=os.environ[
            "RESEND_API_KEY"
        ],
        sender_email=os.environ[
            "PRIVACY_APPROVAL_EMAIL_FROM"
        ],
    )

    # ------------------------------------------------------------------
    # 4. Build the REAL PrivacyApprovalEmailService.
    # ------------------------------------------------------------------

    approval_email_service = (
        PrivacyApprovalEmailService(
            sender=resend_sender,
            approval_recipient=os.environ[
                "PRIVACY_APPROVAL_EMAIL_TO"
            ],
        )
    )

    # ------------------------------------------------------------------
    # 5. Build the REAL governance registry and gate.
    # ------------------------------------------------------------------

    registry = PrivacyChangeRegistry()

    gate = PrivacyGovernanceGate(
        registry=registry,
        validation_service=validation_service,
        approval_email_service=approval_email_service,
    )

    change = _build_change()

    # ------------------------------------------------------------------
    # 6. Execute the REAL governance flow.
    # ------------------------------------------------------------------

    result = await gate.route_and_escalate(
        change
    )

    # ------------------------------------------------------------------
    # 7. Verify the change identity.
    # ------------------------------------------------------------------

    assert (
        result.change_id
        == CHANGE_ID
    )

    # ------------------------------------------------------------------
    # 8. Verify the governance state.
    # ------------------------------------------------------------------

    assert (
        result.status
        == PrivacyChangeStatus.PENDING_DPO_GRC
    )

    # ------------------------------------------------------------------
    # 9. CRITICAL GOVERNANCE CONTROL:
    #
    #    Email delivery must NOT approve the change.
    # ------------------------------------------------------------------

    assert (
        result.status
        != PrivacyChangeStatus.APPROVED
    )

    assert (
        gate.can_proceed(
            CHANGE_ID
        )
        is False
    )

    # ------------------------------------------------------------------
    # 10. Verify that the change exists in the registry.
    # ------------------------------------------------------------------

    registered = registry.get(
        CHANGE_ID
    )

    assert registered is not None

    assert (
        registered.status
        == PrivacyChangeStatus.PENDING_DPO_GRC
    )

    # ------------------------------------------------------------------
    # 11. Controlled success output.
    #
    #     ResendApprovalEmailSender raises an exception if the
    #     Resend delivery call fails. Therefore reaching this point
    #     means the provider call completed without an exception.
    # ------------------------------------------------------------------

    print(
        "\n"
        "============================================================\n"
        "PRIVACY GOVERNANCE RESEND E2E TEST PASSED\n"
        "============================================================\n"
        f"Change ID: {CHANGE_ID}\n"
        f"Validation: {validation.status}\n"
        f"Checks: {validation.checks}\n"
        f"Passed: {validation.passed}\n"
        "DPO required: YES\n"
        "GRC required: YES\n"
        "Governance status: PENDING_DPO_GRC\n"
        "Email delivery: Resend accepted without exception\n"
        "Governance approval: NOT GRANTED\n"
        "============================================================\n"
    )
