from __future__ import annotations

"""Controlled Beta 1 Processing Activity composition.

This module composes the existing canonical ProcessingActivity /
ProcessingRegistry capability. Validation fixtures remain separate.
"""

from .processing_activity import ProcessingActivity
from .processing_registry import ProcessingRegistry

BETA1_TELEGRAM_PROCESSING_ID = "PA-BETA1-001"


def create_beta1_processing_registry() -> ProcessingRegistry:
    """Create the controlled Beta 1 processing registry."""
    activity = ProcessingActivity(
        processing_id=BETA1_TELEGRAM_PROCESSING_ID,
        name="Beta 1 Telegram conversation processing",
        purpose="Beta 1 Telegram learning conversations.",
        data_categories=(
            "identity/account data",
            "Telegram conversation content",
            "learning interaction data",
        ),
        data_subjects=("Beta learners",),
        source=("Telegram",),
        destinations=("EasyChatBot application", "LLM provider"),
        legal_basis="PENDING_DPO_LEGAL",
        retention_id="PENDING_DPO_GRC",
        processor_ids=(),
        data_map_id="",
        dpia_screening_id="",
        gdpr_references=(),
        security_controls=(),
        metadata={
            "governance_status": "PENDING_DPO_GRC",
            "legal_materiality_established": False,
            "material_change_detected": False,
            "special_category_data": False,
            "transfer_status": "PENDING_DPO_GRC",
            "last_material_change_at": None,
        },
        approval_status="PENDING",
    )
    return ProcessingRegistry([activity])


__all__ = ["BETA1_TELEGRAM_PROCESSING_ID", "create_beta1_processing_registry"]
