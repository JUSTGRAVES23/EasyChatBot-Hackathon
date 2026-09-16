from __future__ import annotations

from .announcement_policy import AnnouncementPolicy
from .models import Announcement, AnnouncementType, ComposedAnnouncement


_TYPE_LABELS: dict[AnnouncementType, str] = {
    AnnouncementType.NEW_FEATURE: "🚀 NEW FEATURE",
    AnnouncementType.MAINTENANCE: "🛠️ MAINTENANCE",
    AnnouncementType.KNOWN_ISSUE: "🐛 KNOWN ISSUE",
    AnnouncementType.INCIDENT: "🚨 INCIDENT",
    AnnouncementType.PLANNED_DOWNTIME: "🕐 PLANNED DOWNTIME",
    AnnouncementType.IMPORTANT: "📢 IMPORTANT",
    AnnouncementType.BETA_TEST: "🧪 BETA TEST",
    AnnouncementType.FEEDBACK: "💬 FEEDBACK",
    AnnouncementType.PRIVACY: "🔐 PRIVACY",
    AnnouncementType.POLICY: "📜 POLICY",
    AnnouncementType.BETA_UPDATE: "🎓 BETA UPDATE",
    AnnouncementType.OTHER: "📌 UPDATE",
}


class AnnouncementComposer:
    """Creates validated, consistent EasyWorld announcement messages."""

    def __init__(
        self,
        *,
        policy: AnnouncementPolicy | None = None,
    ) -> None:
        self._policy = policy or AnnouncementPolicy()

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

        parts = [
            _TYPE_LABELS[announcement_type],
            "",
            f"**{announcement.title.strip()}**",
            "",
            announcement.body.strip(),
        ]

        if announcement.footer:
            parts.extend(["", announcement.footer.strip()])

        parts.extend(["", "🌱 *EasyWorld — Growing with You*"])

        return ComposedAnnouncement(
            announcement=announcement,
            rendered_text="\n".join(parts),
        )
