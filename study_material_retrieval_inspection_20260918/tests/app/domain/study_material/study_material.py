from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class StudyMaterialType(str, Enum):
    """
    Controlled classification of learner-facing study materials.

    The initial catalogue deliberately remains small.

    Future material types must be introduced through an explicit
    domain change rather than accepting arbitrary strings.
    """

    READING = "READING"
    LESSON = "LESSON"
    EXERCISE = "EXERCISE"


class StudyMaterialStatus(str, Enum):
    """
    Controlled lifecycle state for Study Material.

    Learner-facing application services must expose only
    PUBLISHED materials.
    """

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True)
class StudyMaterial:
    """
    Immutable learner-facing Study Material catalogue entity.

    StudyMaterial represents the metadata and catalogue identity
    of material belonging to a Learning World.

    It deliberately does NOT contain:

    - learner identity
    - Telegram identity
    - conversation identity
    - AI-generated content
    - RAG state
    - file-storage state
    - learner progress
    - mastery state

    Content/versioning will be introduced as a separate model when
    the content lifecycle is implemented.
    """

    material_id: UUID
    world_id: str
    title: str
    description: str | None
    material_type: StudyMaterialType
    status: StudyMaterialStatus
    display_order: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """
        Validate the Study Material domain invariants.
        """

        if not isinstance(self.material_id, UUID):
            raise ValueError(
                "material_id must be a UUID."
            )

        if not isinstance(self.world_id, str):
            raise ValueError(
                "world_id must be a string."
            )

        if not self.world_id.strip():
            raise ValueError(
                "world_id cannot be empty."
            )

        if not isinstance(self.title, str):
            raise ValueError(
                "title must be a string."
            )

        if not self.title.strip():
            raise ValueError(
                "title cannot be empty."
            )

        if self.description is not None:
            if not isinstance(self.description, str):
                raise ValueError(
                    "description must be a string or None."
                )

        if not isinstance(
            self.material_type,
            StudyMaterialType,
        ):
            raise ValueError(
                "material_type must be a StudyMaterialType."
            )

        if not isinstance(
            self.status,
            StudyMaterialStatus,
        ):
            raise ValueError(
                "status must be a StudyMaterialStatus."
            )

        if not isinstance(self.display_order, int):
            raise ValueError(
                "display_order must be an integer."
            )

        if isinstance(self.display_order, bool):
            raise ValueError(
                "display_order must be an integer."
            )

        if self.display_order < 0:
            raise ValueError(
                "display_order cannot be negative."
            )

        if not isinstance(self.created_at, datetime):
            raise ValueError(
                "created_at must be a datetime."
            )

        if not isinstance(self.updated_at, datetime):
            raise ValueError(
                "updated_at must be a datetime."
            )

        if self.updated_at < self.created_at:
            raise ValueError(
                "updated_at cannot be earlier than created_at."
            )


__all__ = [
    "StudyMaterial",
    "StudyMaterialStatus",
    "StudyMaterialType",
]