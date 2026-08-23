from dataclasses import dataclass
from datetime import datetime, timezone
from .approval_status import ApprovalStatus


@dataclass
class ApprovalRequest:
    approval_id: str
    action: str
    component: str
    reason: str
    requested_by: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = datetime.now(timezone.utc)
