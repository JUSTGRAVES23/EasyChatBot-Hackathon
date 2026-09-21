from __future__ import annotations

from datetime import datetime, timezone

from .domain import EmailWorkflowLifecycle
from .registry import EmailWorkflowRegistry


class EmailWorkflowLifecycleService:
    """Application service for controlled workflow lifecycle changes."""

    def __init__(self, registry: EmailWorkflowRegistry) -> None:
        self._registry = registry

    def pause(self, workflow_id: str):
        workflow = self._require(workflow_id)

        if not workflow.can_pause():
            raise ValueError(
                f"Workflow cannot be paused: {workflow_id}"
            )

        return self._change(
            workflow_id,
            EmailWorkflowLifecycle.PAUSED,
        )

    def resume(self, workflow_id: str):
        workflow = self._require(workflow_id)

        if not workflow.can_resume():
            raise ValueError(
                f"Workflow cannot be resumed: {workflow_id}"
            )

        return self._change(
            workflow_id,
            EmailWorkflowLifecycle.ACTIVE,
        )

    def disable(self, workflow_id: str):
        workflow = self._require(workflow_id)

        if not workflow.can_disable():
            raise ValueError(
                f"Workflow cannot be disabled: {workflow_id}"
            )

        return self._change(
            workflow_id,
            EmailWorkflowLifecycle.DISABLED,
        )

    def enable(self, workflow_id: str):
        workflow = self._require(workflow_id)

        if not workflow.can_enable():
            raise ValueError(
                f"Workflow cannot be enabled: {workflow_id}"
            )

        return self._change(
            workflow_id,
            EmailWorkflowLifecycle.ACTIVE,
        )

    def archive(self, workflow_id: str):
        workflow = self._require(workflow_id)

        if not workflow.can_archive():
            raise ValueError(
                f"Workflow cannot be archived: {workflow_id}"
            )

        return self._change(
            workflow_id,
            EmailWorkflowLifecycle.ARCHIVED,
        )

    def _require(self, workflow_id: str):
        workflow = self._registry.get(workflow_id)

        if workflow is None:
            raise KeyError(
                f"Workflow not found: {workflow_id}"
            )

        return workflow

    def _change(
        self,
        workflow_id: str,
        lifecycle: EmailWorkflowLifecycle,
    ):
        workflow = self._registry.get(workflow_id)

        if workflow is None:
            raise KeyError(
                f"Workflow not found: {workflow_id}"
            )

        now = datetime.now(timezone.utc)

        updated = workflow.with_lifecycle(lifecycle)

        updated = type(updated)(
            workflow_id=updated.workflow_id,
            name=updated.name,
            description=updated.description,
            workflow_type=updated.workflow_type,
            lifecycle=updated.lifecycle,
            owner=updated.owner,
            trigger=updated.trigger,
            schedule=updated.schedule,
            template_id=updated.template_id,
            version=updated.version,
            created_at=updated.created_at,
            updated_at=now,
        )

        return self._registry.update(updated)
