from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class PublicationType(str, Enum):
    NEW_FEATURE = "new_feature"
    MAINTENANCE = "maintenance"
    KNOWN_ISSUE = "known_issue"
    INCIDENT = "incident"
    PLANNED_DOWNTIME = "planned_downtime"
    IMPORTANT = "important"
    BETA_TEST = "beta_test"
    PRIVACY = "privacy"
    POLICY = "policy"
    BETA_UPDATE = "beta_update"


class PublicationStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class AnnouncementTemplateVersion:
    template_id: str
    version: int
    publication_type: PublicationType
    structure: tuple[str, ...]
    required_fields: frozenset[str] = frozenset()
    optional_fields: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.template_id.strip():
            raise ValueError("template_id cannot be empty.")
        if self.version < 1:
            raise ValueError("version must be >= 1.")
        if not self.structure:
            raise ValueError("structure cannot be empty.")

        declared = set(self.required_fields) | set(self.optional_fields)
        for token in self.structure:
            if token.startswith("{{") and token.endswith("}}"):
                name = token[2:-2].strip()
                if name and name not in declared:
                    raise ValueError(f"Template field '{name}' is not declared.")


@dataclass(frozen=True)
class AnnouncementTemplate:
    template_id: str
    name: str
    publication_type: PublicationType
    active_version: int
    versions: tuple[AnnouncementTemplateVersion, ...] = field(default_factory=tuple)
    description: str = ""
    category: str | None = None

    def get_version(self, version: int | None = None) -> AnnouncementTemplateVersion:
        target = self.active_version if version is None else version
        for item in self.versions:
            if item.version == target:
                return item
        raise ValueError(
            f"Template '{self.template_id}' version {target} does not exist."
        )


def render_template(
    template: AnnouncementTemplateVersion,
    values: Mapping[str, str],
) -> str:
    missing = sorted(
        name
        for name in template.required_fields
        if not values.get(name, "").strip()
    )
    if missing:
        raise ValueError("Missing required template fields: " + ", ".join(missing))

    rendered: list[str] = []
    for token in template.structure:
        if token.startswith("{{") and token.endswith("}}"):
            name = token[2:-2].strip()
            value = values.get(name, "")
            if value:
                rendered.append(value.strip())
        else:
            rendered.append(token)

    return "\n".join(part for part in rendered if part).strip()
