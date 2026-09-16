"""
Cybersecurity Scheduler Factory.

Creates the single shared scheduler runtime.

Academy is composed as an optional application workflow and
registered on the existing scheduler. No second scheduler is created.
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from cybersecurity.scheduler.cybersecurity_scheduler_runtime import (
    CybersecuritySchedulerRuntime,
)

from cybersecurity.scheduler.cybersecurity_apscheduler_adapter import (
    CybersecurityAPSchedulerAdapter,
)

from cybersecurity.scheduler.scheduler_configuration import (
    SCHEDULER_TIMEZONE,
)

from cybersecurity.scheduler.cybersecurity_scheduler_workflow import (
    CybersecuritySchedulerWorkflow,
)

from cybersecurity.email.cybersecurity_email_service import (
    CybersecurityEmailService,
)

from app.application.composition.academy_production import (
    create_academy_one_week_workflow,
)


def create_cybersecurity_scheduler_runtime(
    workflow_service=None,
    *,
    academy_one_week_workflow=None,
) -> CybersecuritySchedulerRuntime:
    """Create the single shared scheduler runtime."""

    if workflow_service is None:
        email_service = CybersecurityEmailService(
            recipient="davdbarbero1999@gmail.com",
        )

        workflow_service = CybersecuritySchedulerWorkflow(
            email_service=email_service,
        )

    scheduler = AsyncIOScheduler(
        timezone=SCHEDULER_TIMEZONE,
    )

    # Academy production composition is explicit and injectable.
    #
    # It is deliberately NOT created here automatically because the
    # application import path must remain safe when PostgreSQL is not
    # configured in a development/test environment.
    #
    # Production composition may inject the completed Academy workflow.

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=workflow_service,
        academy_one_week_workflow=academy_one_week_workflow,
    )

    return CybersecuritySchedulerRuntime(
        scheduler_adapter=adapter,
    )


__all__ = [
    "create_cybersecurity_scheduler_runtime",
]

