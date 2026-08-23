from fastapi import APIRouter, HTTPException

from backend.governance.change_management.change_management_service import (
    ChangeManagementService,
)
from backend.governance.change_management.change_risk import ChangeRisk
from backend.governance.change_management.change_type import ChangeType


router = APIRouter(
    prefix="/governance/changes",
    tags=["Governance Change Management"],
)


service = ChangeManagementService()


@router.post("")
async def create_change(payload: dict):

    required = (
        "component",
        "action",
        "reason",
        "requested_by",
        "change_type",
        "risk",
    )

    missing = [
        field
        for field in required
        if field not in payload
    ]

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing fields: {missing}",
        )

    try:
        change_type = ChangeType(payload["change_type"])
        risk = ChangeRisk(payload["risk"])
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    record = service.create_change(
        component=payload["component"],
        action=payload["action"],
        reason=payload["reason"],
        requested_by=payload["requested_by"],
        change_type=change_type,
        risk=risk,
        approval_id=payload.get("approval_id"),
    )

    return _serialize(record)


@router.get("")
async def list_changes():
    return {
        "changes": [
            _serialize(record)
            for record in service.list_records()
        ]
    }


def _serialize(record):
    return {
        "change_id": record.change_id,
        "approval_id": record.approval_id,
        "change_type": record.change_type.value,
        "component": record.component,
        "action": record.action,
        "reason": record.reason,
        "requested_by": record.requested_by,
        "risk": record.risk.value,
        "status": record.status.value,
        "created_at": record.created_at.isoformat(),
    }
