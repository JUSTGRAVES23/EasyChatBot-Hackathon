from __future__ import annotations

from .privacy_approval_record import PrivacyApprovalRecord


class PrivacyApprovalRegistry:
    """Registry for explicit human approval/rejection evidence."""

    def __init__(
        self,
        records: list[PrivacyApprovalRecord] | None = None,
    ) -> None:
        self._records: dict[str, PrivacyApprovalRecord] = {}
        for record in records or []:
            self.register(record)

    def register(self, record: PrivacyApprovalRecord) -> None:
        if record.approval_id in self._records:
            raise ValueError(
                f"Approval record already registered: {record.approval_id}"
            )
        self._records[record.approval_id] = record

    def get(self, approval_id: str) -> PrivacyApprovalRecord:
        try:
            return self._records[approval_id]
        except KeyError as exc:
            raise KeyError(
                f"Approval record not registered: {approval_id}"
            ) from exc

    def for_case(self, case_id: str) -> tuple[PrivacyApprovalRecord, ...]:
        return tuple(
            record
            for record in self._records.values()
            if record.case_id == case_id
        )

    def all(self) -> tuple[PrivacyApprovalRecord, ...]:
        return tuple(self._records.values())
