from __future__ import annotations

from .models import Announcement


class AnnouncementPolicyError(ValueError):
    """Raised when an announcement violates publication policy."""


class AnnouncementPolicy:
    """Beta 1 validation boundary for administrator-controlled announcements."""

    MAX_TITLE_LENGTH = 120
    MAX_BODY_LENGTH = 1800
    MAX_FOOTER_LENGTH = 300

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

        if (
            announcement.footer is not None
            and len(announcement.footer) > self.MAX_FOOTER_LENGTH
        ):
            raise AnnouncementPolicyError(
                "Announcement footer exceeds the Beta 1 limit."
            )
