from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AnnouncementType(StrEnum):
    NEW_FEATURE = "new_feature"
    MAINTENANCE = "maintenance"
    KNOWN_ISSUE = "known_issue"
    INCIDENT = "incident"
    PLANNED_DOWNTIME = "planned_downtime"
    IMPORTANT = "important"
    BETA_TEST = "beta_test"
    FEEDBACK = "feedback"
    PRIVACY = "privacy"
    POLICY = "policy"
    BETA_UPDATE = "beta_update"
    OTHER = "other"


@dataclass(frozen=True)
class Announcement:
    announcement_type: AnnouncementType
    title: str
    body: str
    footer: str | None = None


class AnnouncementPolicyError(ValueError):
    """Raised when an announcement violates publication policy."""


class AnnouncementPolicy:
    """Beta 1 publication guard.

    The policy intentionally remains simple. Beta 1 has no CMS and no
    autonomous publishing.
    """

    MAX_TITLE_LENGTH = 120
    MAX_BODY_LENGTH = 1800

    def validate(self, announcement: Announcement) -> None:
        if not announcement.title.strip():
            raise AnnouncementPolicyError("Announcement title is required.")

        if not announcement.body.strip():
            raise AnnouncementPolicyError("Announcement body is required.")

        if len(announcement.title) > self.MAX_TITLE_LENGTH:
            raise AnnouncementPolicyError(
                "Announcement title exceeds the Beta 1 limit."
            )

        if len(announcement.body) > self.MAX_BODY_LENGTH:
            raise AnnouncementPolicyError(
                "Announcement body exceeds the Beta 1 limit."
            )

        if announcement.footer and len(announcement.footer) > 300:
            raise AnnouncementPolicyError(
                "Announcement footer exceeds the Beta 1 limit."
            )
