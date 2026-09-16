from fastapi import APIRouter

from governance.timeline.governance_timeline_service import (
    GovernanceTimelineService,
)


router = APIRouter(
    prefix="/governance/timeline",
    tags=["Governance Timeline"],
)


timeline_service = GovernanceTimelineService()


@router.get("")
async def get_timeline():

    return {
        "events": [
            {
                "event_id": item.event_id,
                "event": item.event,
                "component": item.component,
                "actor": item.actor,
                "reason": item.reason,
                "severity": item.severity,
                "evidence_available": item.evidence_available,
                "timestamp": item.timestamp.isoformat(),
            }
            for item in timeline_service.list_events()
        ]
    }

