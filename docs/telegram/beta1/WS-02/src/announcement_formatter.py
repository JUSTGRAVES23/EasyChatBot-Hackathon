from __future__ import annotations

from .announcement_policy import Announcement, AnnouncementType


TYPE_LABELS: dict[AnnouncementType, str] = {
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


class AnnouncementFormatter:
    """Creates the compact EasyWorld branded Telegram message."""

    def format(self, announcement: Announcement) -> str:
        label = TYPE_LABELS[announcement.announcement_type]

        parts = [
            label,
            "",
            f"**{announcement.title.strip()}**",
            "",
            announcement.body.strip(),
        ]

        if announcement.footer:
            parts.extend(["", announcement.footer.strip()])

        parts.extend(["", "🌱 *EasyWorld — Growing with You*"])

        return "\n".join(parts)
