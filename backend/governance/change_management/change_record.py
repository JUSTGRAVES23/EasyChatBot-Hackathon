from dataclasses import dataclass, field
from datetime import datetime, timezone

from .change_risk import ChangeRisk
from .change_status import ChangeStatus
from .change_type import ChangeType


@dataclass(frozen=True)
class ChangeRecord:
    change_id: str
    approval_id: str | None
    change_type: ChangeType
    component: str
    action: str
    reason: str
    requested_by: str
    risk: ChangeRisk
    status: ChangeStatus = ChangeStatus.PROPOSED
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
