from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .domain import EmailWorkflowDefinition, EmailWorkflowLifecycle, EmailWorkflowType
from .registry import EmailWorkflowRegistry


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    created: tuple[str, ...]
    already_present: tuple[str, ...]


BUILT_IN_EMAIL_WORKFLOWS: tuple[dict[str, object], ...] = (
    {
        "workflow_id": "cybersecurity_daily_report",
        "name": "Cybersecurity Daily Report",
        "description": "Scheduled daily cybersecurity report email workflow.",
        "workflow_type": EmailWorkflowType.SCHEDULED,
        "lifecycle": EmailWorkflowLifecycle.ACTIVE,
        "owner": "cybersecurity",
        "trigger": "scheduled",
        "schedule": "daily_08:00",
        "template_id": "cybersecurity_daily_report",
    },
    {
        "workflow_id": "cybersecurity_weekly_report",
        "name": "Cybersecurity Weekly Report",
        "description": "Scheduled weekly cybersecurity report email workflow.",
        "workflow_type": EmailWorkflowType.SCHEDULED,
        "lifecycle": EmailWorkflowLifecycle.ACTIVE,
        "owner": "cybersecurity",
        "trigger": "scheduled",
        "schedule": "weekly_monday_08:00",
        "template_id": "cybersecurity_weekly_report",
    },
    {
        "workflow_id": "cybersecurity_critical_alert",
        "name": "Cybersecurity Critical Alert",
        "description": "Event-driven critical cybersecurity alert email workflow.",
        "workflow_type": EmailWorkflowType.EVENT_DRIVEN,
        "lifecycle": EmailWorkflowLifecycle.ACTIVE,
        "owner": "cybersecurity",
        "trigger": "critical_event",
        "schedule": None,
        "template_id": "cybersecurity_critical_alert",
    },
)


class EmailWorkflowRegistryBootstrap:
    def __init__(self, registry: EmailWorkflowRegistry) -> None:
        if registry is None:
            raise ValueError("registry is required.")
        self._registry = registry

    def ensure_registered(self, *, now: datetime | None = None) -> BootstrapResult:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("now must be timezone-aware.")

        created: list[str] = []
        already_present: list[str] = []

        for raw in BUILT_IN_EMAIL_WORKFLOWS:
            workflow_id = str(raw["workflow_id"])
            if self._registry.get(workflow_id) is not None:
                already_present.append(workflow_id)
                continue

            workflow = EmailWorkflowDefinition(
                workflow_id=workflow_id,
                name=str(raw["name"]),
                description=str(raw["description"]),
                workflow_type=raw["workflow_type"],  # type: ignore[arg-type]
                lifecycle=raw["lifecycle"],  # type: ignore[arg-type]
                owner=str(raw["owner"]),
                trigger=str(raw["trigger"]),
                schedule=str(raw["schedule"]) if raw["schedule"] is not None else None,
                template_id=str(raw["template_id"]),
                version=1,
                created_at=current,
                updated_at=current,
            )
            self._registry.create(workflow)
            created.append(workflow_id)

        return BootstrapResult(
            created=tuple(created),
            already_present=tuple(already_present),
        )


__all__ = ["BootstrapResult", "BUILT_IN_EMAIL_WORKFLOWS", "EmailWorkflowRegistryBootstrap"]
