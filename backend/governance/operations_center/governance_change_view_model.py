class GovernanceChangeViewModel:

    def build(self, record) -> dict:
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


    def build_collection(self, records) -> list[dict]:
        return [
            self.build(record)
            for record in records
        ]
