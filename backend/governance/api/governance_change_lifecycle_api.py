from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/governance/change-lifecycle",
    tags=["Governance Change Lifecycle"],
)


@router.post("/{change_id}/approve")
async def approve_change(change_id: str):
    return {
        "change_id": change_id,
        "status": "APPROVED",
        "audit_event": "CHANGE_APPROVED",
    }


@router.post("/{change_id}/reject")
async def reject_change(change_id: str):
    return {
        "change_id": change_id,
        "status": "REJECTED",
        "audit_event": "CHANGE_REJECTED",
    }
