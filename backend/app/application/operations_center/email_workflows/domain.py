from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class EmailWorkflowType(StrEnum):
    SCHEDULED = "SCHEDULED"
    EVENT_DRIVEN = "EVENT_DRIVEN"
    MANUAL = "MANUAL"
    SYSTEM = "SYSTEM"


class EmailWorkflowLifecycle(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True)
class EmailWorkflowDefinition:
    workflow_id: str
    name: str
    description: str
    workflow_type: EmailWorkflowType
    lifecycle: EmailWorkflowLifecycle
    owner: str
    trigger: str
    schedule: str | None
    template_id: str
    version: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.workflow_id.strip():
            raise ValueError("workflow_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if not self.owner.strip():
            raise ValueError("owner must not be empty")
        if not self.trigger.strip():
            raise ValueError("trigger must not be empty")
        if not self.template_id.strip():
            raise ValueError("template_id must not be empty")
        if self.version < 1:
            raise ValueError("version must be >= 1")

        if (
            self.workflow_type is EmailWorkflowType.SCHEDULED
            and not self.schedule
        ):
            raise ValueError(
                "SCHEDULED workflows must define a schedule"
            )

        if (
            self.workflow_type is not EmailWorkflowType.SCHEDULED
            and self.schedule is not None
        ):
            raise ValueError(
                "Only SCHEDULED workflows may define a schedule"
            )

    def can_pause(self) -> bool:
        return (
            self.lifecycle is EmailWorkflowLifecycle.ACTIVE
            and self.workflow_type is EmailWorkflowType.SCHEDULED
        )

    def can_resume(self) -> bool:
        return self.lifecycle is EmailWorkflowLifecycle.PAUSED

    def can_disable(self) -> bool:
        return self.lifecycle in {
            EmailWorkflowLifecycle.ACTIVE,
            EmailWorkflowLifecycle.PAUSED,
        }

    def can_enable(self) -> bool:
        return self.lifecycle is EmailWorkflowLifecycle.DISABLED

    def can_archive(self) -> bool:
        return self.lifecycle is not EmailWorkflowLifecycle.ARCHIVED

    def with_lifecycle(
        self,
        lifecycle: EmailWorkflowLifecycle,
    ) -> EmailWorkflowDefinition:
        return EmailWorkflowDefinition(
            workflow_id=self.workflow_id,
            name=self.name,
            description=self.description,
            workflow_type=self.workflow_type,
            lifecycle=lifecycle,
            owner=self.owner,
            trigger=self.trigger,
            schedule=self.schedule,
            template_id=self.template_id,
            version=self.version + 1,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
