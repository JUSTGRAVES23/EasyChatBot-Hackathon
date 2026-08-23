"""
Governance Evidence API.

Read-only audit evidence projection.

Uses the shared governance audit service.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends

from backend.governance.operations_center.governance_evidence_service import (
    GovernanceEvidenceService,
)

from backend.governance.operations_center.governance_runtime import (
    governance_evidence_service,
)


router = APIRouter(
    prefix="/operations/governance",
    tags=["Governance Evidence"],
)


def get_evidence_service() -> GovernanceEvidenceService:
    return governance_evidence_service


@router.get("/timeline")
async def governance_timeline(
    service: GovernanceEvidenceService = Depends(
        get_evidence_service,
    ),
) -> dict:
    """Return shared governance audit evidence."""

    return {
        "events": service.timeline(),
    }