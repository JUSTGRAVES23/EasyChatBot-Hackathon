from __future__ import annotations

from collections.abc import Sequence

from .domain import EmailWorkflowDefinition
from .registry import EmailWorkflowRegistry


class InMemoryEmailWorkflowRegistry(EmailWorkflowRegistry):
    """Deterministic registry implementation used by unit tests and composition.

    Persistence will be introduced in a later vertical slice.
    """

    def __init__(self) -> None:
        self._workflows: dict[str, EmailWorkflowDefinition] = {}

    def create(
        self,
        workflow: EmailWorkflowDefinition,
    ) -> EmailWorkflowDefinition:
        if workflow.workflow_id in self._workflows:
            raise ValueError(
                f"Workflow already exists: {workflow.workflow_id}"
            )

        self._workflows[workflow.workflow_id] = workflow
        return workflow

    def get(
        self,
        workflow_id: str,
    ) -> EmailWorkflowDefinition | None:
        return self._workflows.get(workflow_id)

    def list(self) -> Sequence[EmailWorkflowDefinition]:
        return tuple(
            sorted(
                self._workflows.values(),
                key=lambda workflow: workflow.workflow_id,
            )
        )

    def update(
        self,
        workflow: EmailWorkflowDefinition,
    ) -> EmailWorkflowDefinition:
        if workflow.workflow_id not in self._workflows:
            raise KeyError(
                f"Workflow not found: {workflow.workflow_id}"
            )

        self._workflows[workflow.workflow_id] = workflow
        return workflow
