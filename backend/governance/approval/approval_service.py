from .approval_status import ApprovalStatus
from .approval_request import ApprovalRequest


class ApprovalService:

    def __init__(self):
        self.requests = []


    def create_request(
        self,
        action: str,
        component: str,
        reason: str,
        requested_by: str,
    ) -> ApprovalRequest:

        request = ApprovalRequest(
            approval_id=f"APR-{len(self.requests)+1:03d}",
            action=action,
            component=component,
            reason=reason,
            requested_by=requested_by,
        )

        self.requests.append(request)

        return request


    def approve(
        self,
        approval_id: str,
    ):

        request = self.get(approval_id)

        request.status = ApprovalStatus.APPROVED

        return request


    def reject(
        self,
        approval_id: str,
    ):

        request = self.get(approval_id)

        request.status = ApprovalStatus.REJECTED

        return request


    def get(self, approval_id: str):

        for request in self.requests:
            if request.approval_id == approval_id:
                return request

        raise ValueError("Approval not found")
