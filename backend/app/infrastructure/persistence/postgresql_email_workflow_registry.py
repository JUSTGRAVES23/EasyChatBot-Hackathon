from __future__ import annotations

from sqlalchemy import select

from app.application.operations_center.email_workflows.domain import (
    EmailWorkflowDefinition,
    EmailWorkflowLifecycle,
    EmailWorkflowType,
)
from app.application.operations_center.email_workflows.registry import (
    EmailWorkflowRegistry,
)

from .email_workflow_models import EmailWorkflowRecord


class PostgreSQLEmailWorkflowRegistry(EmailWorkflowRegistry):
    """PostgreSQL implementation of the authoritative email workflow registry."""

    def __init__(self, session_factory) -> None:
        if session_factory is None:
            raise ValueError("session_factory is required.")

        self._session_factory = session_factory

    def create(
        self,
        workflow: EmailWorkflowDefinition,
    ) -> EmailWorkflowDefinition:
        if workflow is None:
            raise ValueError("workflow is required.")

        with self._session_factory() as session:
            existing = session.get(
                EmailWorkflowRecord,
                workflow.workflow_id,
            )

            if existing is not None:
                raise ValueError(
                    f"Workflow already exists: {workflow.workflow_id}"
                )

            session.add(self._to_record(workflow))
            session.commit()

        return workflow

    def get(
        self,
        workflow_id: str,
    ) -> EmailWorkflowDefinition | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(EmailWorkflowRecord).where(
                    EmailWorkflowRecord.workflow_id == workflow_id,
                )
            )

        if record is None:
            return None

        return self._to_domain(record)

    def list(self):
        with self._session_factory() as session:
            records = session.scalars(
                select(EmailWorkflowRecord).order_by(
                    EmailWorkflowRecord.workflow_id.asc(),
                )
            ).all()

        return [self._to_domain(record) for record in records]

    def update(
        self,
        workflow: EmailWorkflowDefinition,
    ) -> EmailWorkflowDefinition:
        if workflow is None:
            raise ValueError("workflow is required.")

        with self._session_factory() as session:
            record = session.get(
                EmailWorkflowRecord,
                workflow.workflow_id,
            )

            if record is None:
                raise KeyError(
                    f"Workflow not found: {workflow.workflow_id}"
                )

            record.name = workflow.name
            record.description = workflow.description
            record.workflow_type = workflow.workflow_type.value
            record.lifecycle = workflow.lifecycle.value
            record.owner = workflow.owner
            record.trigger = workflow.trigger
            record.schedule = workflow.schedule
            record.template_id = workflow.template_id
            record.version = workflow.version
            record.updated_at = workflow.updated_at

            session.commit()

        return workflow

    @staticmethod
    def _to_record(
        workflow: EmailWorkflowDefinition,
    ) -> EmailWorkflowRecord:
        return EmailWorkflowRecord(
            workflow_id=workflow.workflow_id,
            name=workflow.name,
            description=workflow.description,
            workflow_type=workflow.workflow_type.value,
            lifecycle=workflow.lifecycle.value,
            owner=workflow.owner,
            trigger=workflow.trigger,
            schedule=workflow.schedule,
            template_id=workflow.template_id,
            version=workflow.version,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
        )

    @staticmethod
    def _to_domain(
        record: EmailWorkflowRecord,
    ) -> EmailWorkflowDefinition:
        return EmailWorkflowDefinition(
            workflow_id=record.workflow_id,
            name=record.name,
            description=record.description,
            workflow_type=EmailWorkflowType(record.workflow_type),
            lifecycle=EmailWorkflowLifecycle(record.lifecycle),
            owner=record.owner,
            trigger=record.trigger,
            schedule=record.schedule,
            template_id=record.template_id,
            version=record.version,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


__all__ = ["PostgreSQLEmailWorkflowRegistry"]
