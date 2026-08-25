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


@dataclass(frozen=True)
class ComposedAnnouncement:
    announcement: Announcement
    rendered_text: str
