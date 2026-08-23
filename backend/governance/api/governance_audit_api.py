"""
Governance Audit API.

Read-only API boundary for governance evidence.

The API exposes the supplied GovernanceAuditService.
It does not create, modify, pause, resume, or execute controls.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.governance.governance_audit_service import (
    GovernanceAuditService,
)


router = APIRouter(
    prefix="/governance/audit",
    tags=["Governance Audit"],
)


_audit_service = GovernanceAuditService()


def get_governance_audit_service() -> GovernanceAuditService:
    """
    Return the application audit service.

    The dependency can be overridden by the application
    composition root and by tests.
    """
    return _audit_service


@router.get("/events")
async def list_audit_events(
    audit_service: GovernanceAuditService = Depends(
        get_governance_audit_service
    ),
) -> dict:
    """
    Return governance audit events in insertion order.
    """

    events = audit_service.list_events()

    return {
        "events": [
            {
                "event": event.event,
                "actor": event.actor,
                "reason": event.reason,
                "component": event.component,
                "timestamp": event.timestamp.isoformat(),
            }
            for event in events
        ],
        "count": len(events),
    }
