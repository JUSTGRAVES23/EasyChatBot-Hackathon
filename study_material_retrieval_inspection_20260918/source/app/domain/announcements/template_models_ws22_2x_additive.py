from __future__ import annotations

# Apply these two optional fields to the existing WS-22.1 AnnouncementTemplate:
#
#     description: str = ""
#     category: str | None = None
#
# They are deliberately optional to preserve all existing WS-22.1 callers.
#
# The complete class declaration should therefore contain:
#
# @dataclass(frozen=True)
# class AnnouncementTemplate:
#     template_id: str
#     name: str
#     publication_type: PublicationType
#     active_version: int
#     versions: tuple[AnnouncementTemplateVersion, ...] = field(default_factory=tuple)
#     description: str = ""
#     category: str | None = None
#
# No other WS-22.1 behavior needs to change.
