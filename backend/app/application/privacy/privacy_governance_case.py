from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PrivacyTriggerType(StrEnum):
    NEW_PROCESSING = "NEW_PROCESSING"
    PROCESSING_CHANGE = "PROCESSING_CHANGE"
    DATA_MAPPING_CHANGE = "DATA_MAPPING_CHANGE"
    RETENTION_CHANGE = "RETENTION_CHANGE"
    PROCESSOR_CHANGE = "PROCESSOR_CHANGE"
    DPIA_CHANGE = "DPIA_CHANGE"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass(frozen=True, slots=True)
class PrivacyGovernanceCase:
    """Case-centric governance record rendered by the Operations Center.

    ``change_id`` is the stable link to the authoritative PrivacyChange.
    It is optional at model level for backward compatibility with older Beta
    fixtures; newly created runtime cases should always populate it.

    Email metadata belongs to the governance case because it represents
    notification/threading evidence for the governance workflow. It does
    not represent a governance decision.

    ``email_message_id``:
        Provider message identifier for the latest/root governance email
        available for threading.

    ``email_thread_id``:
        Stable identifier for the governance email conversation/thread.
        For the initial implementation this may be the same as the root
        provider message identifier.

    These fields are optional to preserve compatibility with existing Beta
    fixtures and cases created before email-thread persistence was introduced.
    """

    case_id: str
    title: str
    summary: str
    trigger_type: PrivacyTriggerType
    triggered_at: datetime
    trigger_source: str

    # Authoritative link to the underlying PrivacyChange.
    change_id: str | None = None

    processing_ids: tuple[str, ...] = ()
    data_map_ids: tuple[str, ...] = ()

    risk: str = "MEDIUM"
    validation_status: str = "PENDING"

    # Governance notification state.
    email_status: str = "NOT_SENT"

    # Provider/thread metadata for governance notification emails.
    #
    # These fields are notification infrastructure metadata only.
    # They must never be interpreted as governance approval evidence.
    email_message_id: str | None = None
    email_thread_id: str | None = None

    # Human governance decision state.
    governance_status: str = "PENDING_DPO_GRC"
    final_decision: str | None = None
    final_decision_at: datetime | None = None

    def __post_init__(self) -> None:
        # ---------------------------------------------------------------
        # Required case identity / descriptive fields
        # ---------------------------------------------------------------

        for field_name in (
            "case_id",
            "title",
            "summary",
            "trigger_source",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{field_name} is required."
                )

        # ---------------------------------------------------------------
        # Authoritative PrivacyChange relationship
        # ---------------------------------------------------------------

        if self.change_id is not None:
            if not isinstance(self.change_id, str):
                raise ValueError(
                    "change_id must be a string when provided."
                )

            if not self.change_id.strip():
                raise ValueError(
                    "change_id cannot be blank when provided."
                )

        # ---------------------------------------------------------------
        # Timestamp integrity
        # ---------------------------------------------------------------

        if not isinstance(self.triggered_at, datetime):
            raise ValueError(
                "triggered_at must be a datetime."
            )

        if self.triggered_at.tzinfo is None:
            raise ValueError(
                "triggered_at must be timezone-aware."
            )

        if self.final_decision_at is not None:
            if not isinstance(self.final_decision_at, datetime):
                raise ValueError(
                    "final_decision_at must be a datetime when provided."
                )

            if self.final_decision_at.tzinfo is None:
                raise ValueError(
                    "final_decision_at must be timezone-aware."
                )

        # ---------------------------------------------------------------
        # Email/thread metadata integrity
        #
        # Provider identifiers are metadata only. They must never be
        # interpreted as approval or rejection evidence.
        # ---------------------------------------------------------------

        if self.email_message_id is not None:
            if not isinstance(self.email_message_id, str):
                raise ValueError(
                    "email_message_id must be a string when provided."
                )

            if not self.email_message_id.strip():
                raise ValueError(
                    "email_message_id cannot be blank when provided."
                )

        if self.email_thread_id is not None:
            if not isinstance(self.email_thread_id, str):
                raise ValueError(
                    "email_thread_id must be a string when provided."
                )

            if not self.email_thread_id.strip():
                raise ValueError(
                    "email_thread_id cannot be blank when provided."
                )


__all__ = [
    "PrivacyGovernanceCase",
    "PrivacyTriggerType",
]