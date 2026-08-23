from .change_record import ChangeRecord
from .change_risk import ChangeRisk
from .change_status import ChangeStatus
from .change_type import ChangeType


class ChangeManagementService:
    """
    Enterprise change-management boundary.

    Supports:
    - Provider changes
    - Model changes
    - Agent changes
    - Configuration changes
    - Security changes
    - Scheduler changes
    - Legacy change creation

    Does NOT execute changes.
    """


    def __init__(
        self,
        audit_service=None,
    ):
        self.records = []
        self.audit_service = audit_service



    def create_change(
        self,
        *,
        component: str,
        action: str,
        approval_id: str | None = None,
        reason: str = "No reason provided",
        requested_by: str = "system",
        change_type: ChangeType = ChangeType.CONFIGURATION,
        risk: ChangeRisk = ChangeRisk.MEDIUM,
    ) -> ChangeRecord:
        """
        Create governed change record.

        Defaults preserve compatibility with
        older callers while supporting the
        enterprise governance model.
        """


        record = ChangeRecord(

            change_id=(
                f"CHG-{len(self.records) + 1:03d}"
            ),

            approval_id=approval_id,

            change_type=change_type,

            component=component,

            action=action,

            reason=reason,

            requested_by=requested_by,

            risk=risk,

            status=(

                ChangeStatus.PENDING_APPROVAL

                if approval_id

                else ChangeStatus.PROPOSED

            ),

        )


        self.records.append(
            record
        )


        if self.audit_service:

            self.audit_service.record(

                event="CHANGE_CREATED",

                actor=requested_by,

                reason=reason,

                component=component,

                metadata={

                    "change_id": record.change_id,

                    "change_type": (
                        change_type.value
                    ),

                    "risk": (
                        risk.value
                    ),

                    "approval_id": approval_id,

                },

            )


        return record



    def mark_approved(
        self,
        change_id: str,
    ) -> ChangeRecord:

        return self._replace_status(
            change_id,
            ChangeStatus.APPROVED,
        )



    def mark_scheduled(
        self,
        change_id: str,
    ) -> ChangeRecord:

        return self._replace_status(
            change_id,
            ChangeStatus.SCHEDULED,
        )



    def mark_executed(
        self,
        change_id: str,
    ) -> ChangeRecord:

        return self._replace_status(
            change_id,
            ChangeStatus.EXECUTED,
        )



    def mark_failed(
        self,
        change_id: str,
    ) -> ChangeRecord:

        return self._replace_status(
            change_id,
            ChangeStatus.FAILED,
        )



    def cancel(
        self,
        change_id: str,
    ) -> ChangeRecord:

        return self._replace_status(
            change_id,
            ChangeStatus.CANCELLED,
        )



    def get(
        self,
        change_id: str,
    ) -> ChangeRecord:

        for record in self.records:

            if record.change_id == change_id:

                return record


        raise ValueError(
            f"Change record not found: {change_id}"
        )



    def get_by_approval_id(
        self,
        approval_id: str,
    ):

        for record in self.records:

            if record.approval_id == approval_id:

                return record


        return None



    def list_records(
        self,
    ) -> list[ChangeRecord]:

        return list(
            self.records
        )



    def _replace_status(
        self,
        change_id: str,
        status: ChangeStatus,
    ) -> ChangeRecord:


        current = self.get(
            change_id
        )


        updated = ChangeRecord(

            change_id=current.change_id,

            approval_id=current.approval_id,

            change_type=current.change_type,

            component=current.component,

            action=current.action,

            reason=current.reason,

            requested_by=current.requested_by,

            risk=current.risk,

            status=status,

            created_at=current.created_at,

        )


        index = self.records.index(
            current
        )


        self.records[index] = updated


        return updated