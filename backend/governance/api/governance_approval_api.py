from fastapi import APIRouter

from backend.governance.approval.approval_service import ApprovalService


router = APIRouter(
    prefix="/governance/approval",
    tags=["Governance Approval"],
)


service = ApprovalService()


@router.post("/request")
async def create_request(payload: dict):

    request = service.create_request(
        action=payload["action"],
        component=payload["component"],
        reason=payload["reason"],
        requested_by=payload["requested_by"],
    )

    return request
