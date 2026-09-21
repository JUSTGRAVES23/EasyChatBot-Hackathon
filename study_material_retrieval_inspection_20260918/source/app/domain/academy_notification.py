from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AcademyNotificationType(StrEnum):
    ONE_WEEK_MILESTONE = "1_WEEK_MILESTONE"


@dataclass(frozen=True, slots=True)
class AcademyNotification:
    notification_type: AcademyNotificationType
    username: str
    portal_url: str

    def __post_init__(self) -> None:
        if not self.username.strip():
            raise ValueError("username cannot be empty.")
        if not self.portal_url.strip():
            raise ValueError("portal_url cannot be empty.")
        if self.notification_type is not AcademyNotificationType.ONE_WEEK_MILESTONE:
            raise ValueError("Unsupported Academy notification type.")
