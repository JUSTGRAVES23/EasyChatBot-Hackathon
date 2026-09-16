from governance.change_management.change_management_service import (
    ChangeManagementService,
)
from governance.change_management.change_status import ChangeStatus


class ApprovalChangeService:
    """Bridge between approval decisions and change lifecycle."""

    def __init__(self, change_service=None, audit_service=None):
        self.change_service = change_service or ChangeManagementService()
        self.audit_service = audit_service

    def approve_change(self, change_id: str, actor: str):
        change = self.change_service.mark_approved(change_id)

        if self.audit_service:
            self.audit_service.record(
                event="CHANGE_APPROVED",
                actor=actor,
                reason="Approval granted",
                component=change.component,
                metadata={"change_id": change_id},
            )

        return change

    def reject_change(self, change_id: str, actor: str):
        change = self.change_service.cancel(change_id)

        if self.audit_service:
            self.audit_service.record(
                event="CHANGE_REJECTED",
                actor=actor,
                reason="Approval rejected",
                component=change.component,
                metadata={"change_id": change_id},
            )

        return change

