from __future__ import annotations

from .data_processing_map import DataProcessingMap, DataProcessingMapEntry
from .dpia_screening import DPIAScreening, DPIAScreeningRegistry
from .processing_activity import ProcessingActivity
from .processing_registry import ProcessingRegistry
from .processor_registry import ProcessorRecord, ProcessorRegistry
from .privacy_validation_service import PrivacyValidationService
from .retention_registry import RetentionRegistry, RetentionRule


def build_beta1_validation_service() -> PrivacyValidationService:
    """Build the deterministic Beta 1 governance validation fixture.

    In production, these records should be loaded from the authoritative
    controlled privacy registry rather than hard-coded.
    """

    activity = ProcessingActivity(
        processing_id="PA-BETA1-001",
        name="Beta 1 Telegram conversation processing",
        purpose="Provide the approved Beta 1 French learning conversation service.",
        data_categories=("conversation content", "pseudonymous identifier"),
        data_subjects=("Beta 1 learner",),
        source=("Telegram",),
        destinations=("EasyChatBot runtime", "approved persistence"),
        legal_basis="PENDING_DPO_LEGAL",
        retention_id="RET-BETA1-CONVERSATION",
        processor_ids=(),
        data_map_id="MAP-BETA1-001",
        dpia_screening_id="DPIA-BETA1-001",
        gdpr_references=(
            "GDPR Art. 5",
            "GDPR Art. 6",
            "GDPR Art. 25",
            "GDPR Art. 30",
            "GDPR Art. 32",
        ),
        security_controls=(
            "pseudonymisation",
            "access control",
            "auditability",
        ),
        approval_status="PENDING",
    )

    processing = ProcessingRegistry([activity])

    maps = DataProcessingMap([
        DataProcessingMapEntry(
            map_id="MAP-BETA1-001",
            processing_id="PA-BETA1-001",
            source="Telegram",
            input_data=("conversation content", "Telegram identifier for runtime access"),
            runtime_processing=("conversation runtime", "privacy pseudonymisation"),
            pseudonymisation="Telegram identifier is pseudonymised before persistence.",
            persistence=("conversation event store",),
            destinations=("EasyChatBot runtime", "approved persistence"),
            third_country_transfer=False,
        )
    ])

    retention = RetentionRegistry([
        RetentionRule(
            retention_id="RET-BETA1-CONVERSATION",
            data_domain="Beta 1 conversation",
            record_type="conversation event",
            retention_period="PENDING_DPO_GRC",
            trigger="PENDING_DPO_GRC",
            deletion_action="PENDING_DPO_GRC",
            legal_policy_basis="PENDING_DPO_LEGAL",
        )
    ])

    processors = ProcessorRegistry([])

    dpia = DPIAScreeningRegistry([
        DPIAScreening(
            screening_id="DPIA-BETA1-001",
            processing_id="PA-BETA1-001",
            overall_risk="PENDING_DPO_GRC",
            dpia_required="PENDING_DPO",
            dpo_assessment="PENDING_DPO",
            grc_assessment="PENDING_GRC",
            status="PENDING",
        )
    ])

    return PrivacyValidationService(
        processing_registry=processing,
        data_processing_map=maps,
        retention_registry=retention,
        processor_registry=processors,
        dpia_registry=dpia,
    )


def main() -> int:
    result = build_beta1_validation_service().validate()
    print(result.status)
    print(f"{result.checks} controls validated")
    print(f"{result.blocking_failures} blocking privacy gaps")

    if result.failures:
        for failure in result.failures:
            print(f"- {failure}")

    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
