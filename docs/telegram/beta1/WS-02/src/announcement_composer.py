from __future__ import annotations

from dataclasses import dataclass

from .announcement_formatter import AnnouncementFormatter
from .announcement_policy import Announcement, AnnouncementPolicy, AnnouncementType


@dataclass(frozen=True)
class ComposedAnnouncement:
    announcement: Announcement
    rendered_text: str


class AnnouncementComposer:
    """Application-level composition for fast, consistent announcements."""

    def __init__(
        self,
        *,
        policy: AnnouncementPolicy | None = None,
        formatter: AnnouncementFormatter | None = None,
    ) -> None:
        self._policy = policy or AnnouncementPolicy()
        self._formatter = formatter or AnnouncementFormatter()

    def compose(
        self,
        *,
        announcement_type: AnnouncementType,
        title: str,
        body: str,
        footer: str | None = None,
    ) -> ComposedAnnouncement:
        announcement = Announcement(
            announcement_type=announcement_type,
            title=title,
            body=body,
            footer=footer,
        )

        self._policy.validate(announcement)

        return ComposedAnnouncement(
            announcement=announcement,
            rendered_text=self._formatter.format(announcement),
        )
