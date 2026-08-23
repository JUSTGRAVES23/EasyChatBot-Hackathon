"""
EasyChatBot AI Operations Center escalation workflow service.

Coordinates the human-in-the-loop escalation lifecycle.

Architecture:

Provider Incident
        |
        v
Escalation Service
        |
        v
Escalation Workflow Service
        |
        +----------------------+
        |                      |
        v                      v
Notification Service     Approval State
        |                      |
        v                      v
Human Notification      Human Decision
                               |
                    +----------+----------+
                    |                     |
                    v                     v
                 APPROVED              REJECTED


Responsibilities:

- coordinate escalation notification preparation;
- track the human approval state;
- record approval/rejection decisions;
- expose workflow state for the Operations Center;
- preserve the audit trail information required by the
  workflow.

Does NOT:

- execute provider changes;
- modify Runtime routing;
- send autonomous operational commands;
- approve recommendations automatically;
- detect provider incidents;
- perform provider failover.

Human approval is mandatory for operational changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from app.application.provider_management.escalation_notification_service import (
    EscalationNotificationResult,
    EscalationNotificationService,
)

from app.application.provider_management.models import (
    ProviderEscalation,
)


class EscalationWorkflowStatus(str, Enum):
    """
    Human-in-the-loop escalation workflow states.
    """

    PENDING_NOTIFICATION = (
        "pending_notification"
    )

    AWAITING_APPROVAL = (
        "awaiting_approval"
    )

    APPROVED = "approved"

    REJECTED = "rejected"


@dataclass(frozen=True)
class EscalationWorkflow:
    """
    Human-in-the-loop escalation workflow record.
    """

    escalation_id: str

    status: EscalationWorkflowStatus

    created_at: datetime

    notification_recipient: str | None = None

    notification_subject: str | None = None

    approved_at: datetime | None = None

    rejected_at: datetime | None = None

    decision_reason: str | None = None


class EscalationWorkflowService:
    """
    Coordinates the escalation notification and approval
    lifecycle.

    The service deliberately does not execute the action
    represented by an approved recommendation.

    Approval means:

        "A human approved this recommendation."

    It does NOT mean:

        "The system has already changed Runtime routing."
    """

    def __init__(
        self,
        notification_service: (
            EscalationNotificationService
        ),
    ) -> None:
        """
        Initialise the escalation workflow service.
        """

        if notification_service is None:
            raise ValueError(
                "Escalation notification service "
                "cannot be None."
            )

        self._notification_service = (
            notification_service
        )

        self._workflows: dict[
            str,
            EscalationWorkflow,
        ] = {}

    def create_workflow(
        self,
        *,
        escalation: ProviderEscalation,
    ) -> EscalationWorkflow:
        """
        Create a workflow awaiting notification.

        No notification is sent at this stage.
        """

        if escalation is None:
            raise ValueError(
                "Provider escalation cannot be None."
            )

        if not escalation.escalation_id.strip():
            raise ValueError(
                "Escalation ID cannot be empty."
            )

        workflow = EscalationWorkflow(
            escalation_id=(
                escalation.escalation_id
            ),
            status=(
                EscalationWorkflowStatus
                .PENDING_NOTIFICATION
            ),
            created_at=datetime.now(
                timezone.utc
            ),
        )

        self._workflows[
            escalation.escalation_id
        ] = workflow

        return workflow

    def prepare_notification(
        self,
        *,
        escalation: ProviderEscalation,
        recipient: str,
    ) -> EscalationNotificationResult:
        """
        Prepare the human notification and move the
        workflow to awaiting approval.

        Email preparation is delegated to the notification
        service.
        """

        if escalation is None:
            raise ValueError(
                "Provider escalation cannot be None."
            )

        workflow = self.get_workflow(
            escalation.escalation_id
        )

        if workflow is None:
            workflow = self.create_workflow(
                escalation=escalation
            )

        if (
            workflow.status
            != EscalationWorkflowStatus
            .PENDING_NOTIFICATION
        ):
            raise ValueError(
                "Escalation workflow is not awaiting "
                "notification."
            )

        notification = (
            self._notification_service
            .prepare_escalation_notification(
                escalation=escalation,
                recipient=recipient,
            )
        )

        updated = EscalationWorkflow(
            escalation_id=(
                workflow.escalation_id
            ),
            status=(
                EscalationWorkflowStatus
                .AWAITING_APPROVAL
            ),
            created_at=workflow.created_at,
            notification_recipient=(
                notification.recipient
            ),
            notification_subject=(
                notification.subject
            ),
            approved_at=None,
            rejected_at=None,
            decision_reason=None,
        )

        self._workflows[
            escalation.escalation_id
        ] = updated

        return notification

    def approve(
        self,
        *,
        escalation_id: str,
        reason: str,
    ) -> EscalationWorkflow:
        """
        Record a human approval.

        This records approval only.

        It does NOT execute the recommended operational
        change.
        """

        workflow = self._require_workflow(
            escalation_id
        )

        if (
            workflow.status
            != EscalationWorkflowStatus
            .AWAITING_APPROVAL
        ):
            raise ValueError(
                "Escalation must be awaiting approval "
                "before it can be approved."
            )

        if not reason.strip():
            raise ValueError(
                "Approval reason cannot be empty."
            )

        approved = EscalationWorkflow(
            escalation_id=(
                workflow.escalation_id
            ),
            status=(
                EscalationWorkflowStatus
                .APPROVED
            ),
            created_at=workflow.created_at,
            notification_recipient=(
                workflow.notification_recipient
            ),
            notification_subject=(
                workflow.notification_subject
            ),
            approved_at=datetime.now(
                timezone.utc
            ),
            rejected_at=None,
            decision_reason=reason.strip(),
        )

        self._workflows[
            escalation_id
        ] = approved

        return approved

    def reject(
        self,
        *,
        escalation_id: str,
        reason: str,
    ) -> EscalationWorkflow:
        """
        Record a human rejection.

        Rejection does not modify provider routing.
        """

        workflow = self._require_workflow(
            escalation_id
        )

        if (
            workflow.status
            != EscalationWorkflowStatus
            .AWAITING_APPROVAL
        ):
            raise ValueError(
                "Escalation must be awaiting approval "
                "before it can be rejected."
            )

        if not reason.strip():
            raise ValueError(
                "Rejection reason cannot be empty."
            )

        rejected = EscalationWorkflow(
            escalation_id=(
                workflow.escalation_id
            ),
            status=(
                EscalationWorkflowStatus
                .REJECTED
            ),
            created_at=workflow.created_at,
            notification_recipient=(
                workflow.notification_recipient
            ),
            notification_subject=(
                workflow.notification_subject
            ),
            approved_at=None,
            rejected_at=datetime.now(
                timezone.utc
            ),
            decision_reason=reason.strip(),
        )

        self._workflows[
            escalation_id
        ] = rejected

        return rejected

    def get_workflow(
        self,
        escalation_id: str,
    ) -> EscalationWorkflow | None:
        """
        Retrieve an escalation workflow.
        """

        if not escalation_id.strip():
            raise ValueError(
                "Escalation ID cannot be empty."
            )

        return self._workflows.get(
            escalation_id
        )

    def list_workflows(
        self,
    ) -> list[EscalationWorkflow]:
        """
        Return all tracked escalation workflows.
        """

        return list(
            self._workflows.values()
        )

    def _require_workflow(
        self,
        escalation_id: str,
    ) -> EscalationWorkflow:
        """
        Retrieve a required workflow.
        """

        workflow = self.get_workflow(
            escalation_id
        )

        if workflow is None:
            raise ValueError(
                f"Escalation workflow not found: "
                f"{escalation_id}"
            )

        return workflow