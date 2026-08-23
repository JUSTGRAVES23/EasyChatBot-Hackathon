"""
EasyChatBot AI Operations Center escalation workflow repository.

Provides the persistence boundary for human-in-the-loop
escalation workflows.

Architecture:

EscalationWorkflowService
        |
        v
EscalationWorkflowRepository
        |
        v
Persistence Adapter
        |
        v
Escalation History


Responsibilities:

- persist escalation workflow state;
- retrieve workflow state;
- list workflow history.

Does NOT:

- create escalations;
- detect provider incidents;
- send emails;
- approve escalations;
- modify Runtime routing;
- execute provider changes.

The repository stores workflow state only.
Business decisions remain in the application services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.provider_management.escalation_workflow_service import (
    EscalationWorkflow,
)


class EscalationWorkflowRepository(ABC):
    """
    Repository contract for escalation workflow persistence.
    """

    @abstractmethod
    def save(
        self,
        workflow: EscalationWorkflow,
    ) -> None:
        """
        Persist an escalation workflow.
        """

        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        escalation_id: str,
    ) -> EscalationWorkflow | None:
        """
        Retrieve a workflow by escalation ID.
        """

        raise NotImplementedError

    @abstractmethod
    def get_all(
        self,
    ) -> list[EscalationWorkflow]:
        """
        Retrieve all workflow records.
        """

        raise NotImplementedError


class InMemoryEscalationWorkflowRepository(
    EscalationWorkflowRepository,
):
    """
    In-memory workflow repository.

    Used for:

    - Hackathon development;
    - unit testing;
    - integration testing;
    - local demonstrations.

    A SQLite/PostgreSQL adapter can replace this implementation
    later without changing the application service contract.
    """

    def __init__(self) -> None:
        self._workflows: dict[
            str,
            EscalationWorkflow,
        ] = {}

    def save(
        self,
        workflow: EscalationWorkflow,
    ) -> None:
        """
        Save or replace a workflow.
        """

        if workflow is None:
            raise ValueError(
                "Escalation workflow cannot be None."
            )

        if not workflow.escalation_id.strip():
            raise ValueError(
                "Escalation ID cannot be empty."
            )

        self._workflows[
            workflow.escalation_id
        ] = workflow

    def get(
        self,
        escalation_id: str,
    ) -> EscalationWorkflow | None:
        """
        Retrieve a workflow by escalation ID.
        """

        if not escalation_id.strip():
            raise ValueError(
                "Escalation ID cannot be empty."
            )

        return self._workflows.get(
            escalation_id
        )

    def get_all(
        self,
    ) -> list[EscalationWorkflow]:
        """
        Return all persisted workflows.

        Results are ordered by creation time so the
        repository can support the Operations Center
        escalation history view.
        """

        return sorted(
            self._workflows.values(),
            key=lambda workflow: (
                workflow.created_at,
                workflow.escalation_id,
            ),
        )