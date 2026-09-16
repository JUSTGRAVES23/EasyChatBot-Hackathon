"""
EasyChatBot AI Operations Center escalation history service.

Provides read-only operational views over escalation
workflow history.

Architecture:

Escalation Workflow Repository
        |
        v
EscalationHistoryService
        |
        +----------------------+
        |                      |
        v                      v
History View             Operations Dashboard
        |
        v
AI Operations Center


Responsibilities:

- retrieve escalation workflow history;
- filter workflows by status;
- filter workflows by escalation ID;
- provide pending approval workflows;
- provide approved workflows;
- provide rejected workflows;
- provide chronological history.

Does NOT:

- create escalations;
- modify workflow state;
- approve escalations;
- reject escalations;
- send emails;
- change Runtime routing;
- execute provider changes.

This is deliberately a read-only application service.
"""

from __future__ import annotations

from app.application.provider_management.escalation_workflow_repository import (
    EscalationWorkflowRepository,
)

from app.application.provider_management.escalation_workflow_service import (
    EscalationWorkflow,
    EscalationWorkflowStatus,
)


class EscalationHistoryService:
    """
    Read-only application service for escalation history.

    The service provides the Operations Center with a
    stable application contract without exposing the
    repository directly to presentation code.
    """

    def __init__(
        self,
        repository: EscalationWorkflowRepository,
    ) -> None:
        """
        Initialise the history service.
        """

        if repository is None:
            raise ValueError(
                "Escalation workflow repository "
                "cannot be None."
            )

        self._repository = repository

    def list_history(
        self,
    ) -> list[EscalationWorkflow]:
        """
        Return the complete escalation workflow history.

        Results are supplied by the repository in
        chronological order.
        """

        return self._repository.get_all()

    def get(
        self,
        escalation_id: str,
    ) -> EscalationWorkflow | None:
        """
        Retrieve one escalation workflow.
        """

        if not escalation_id.strip():
            raise ValueError(
                "Escalation ID cannot be empty."
            )

        return self._repository.get(
            escalation_id
        )

    def list_by_status(
        self,
        status: EscalationWorkflowStatus,
    ) -> list[EscalationWorkflow]:
        """
        Return workflows matching a specific lifecycle state.
        """

        if status is None:
            raise ValueError(
                "Workflow status cannot be None."
            )

        return [
            workflow
            for workflow in self._repository.get_all()
            if workflow.status == status
        ]

    def list_pending_approval(
        self,
    ) -> list[EscalationWorkflow]:
        """
        Return escalations currently awaiting human approval.
        """

        return self.list_by_status(
            EscalationWorkflowStatus
            .AWAITING_APPROVAL
        )

    def list_approved(
        self,
    ) -> list[EscalationWorkflow]:
        """
        Return approved escalation workflows.
        """

        return self.list_by_status(
            EscalationWorkflowStatus
            .APPROVED
        )

    def list_rejected(
        self,
    ) -> list[EscalationWorkflow]:
        """
        Return rejected escalation workflows.
        """

        return self.list_by_status(
            EscalationWorkflowStatus
            .REJECTED
        )

    def list_pending_notification(
        self,
    ) -> list[EscalationWorkflow]:
        """
        Return workflows waiting for notification preparation.
        """

        return self.list_by_status(
            EscalationWorkflowStatus
            .PENDING_NOTIFICATION
        )

    def count_by_status(
        self,
    ) -> dict[
        EscalationWorkflowStatus,
        int,
    ]:
        """
        Return workflow counts grouped by lifecycle status.

        Example:

            {
                AWAITING_APPROVAL: 2,
                APPROVED: 5,
                REJECTED: 1,
                PENDING_NOTIFICATION: 1,
            }

        All statuses are returned, including zero counts.
        """

        counts = {
            status: 0
            for status in EscalationWorkflowStatus
        }

        for workflow in self._repository.get_all():
            counts[
                workflow.status
            ] += 1

        return counts

    def has_pending_approval(
        self,
    ) -> bool:
        """
        Return whether any escalation currently requires
        human approval.
        """

        return bool(
            self.list_pending_approval()
        )