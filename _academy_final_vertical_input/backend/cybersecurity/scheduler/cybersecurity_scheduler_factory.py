"""
Cybersecurity Scheduler Factory.

Creates the cybersecurity scheduler runtime stack.

Composition:

Factory
    |
    +--> APScheduler Infrastructure
    |
    +--> APScheduler Adapter
    |
    +--> Scheduler Runtime
    |
    +--> Workflow
            |
            +--> Report Service
            |
            +--> Email Service


Does NOT:
- execute cybersecurity decisions;
- send emails directly;
- perform remediation.
"""

from __future__ import annotations



from apscheduler.schedulers.asyncio import (
    AsyncIOScheduler,
)



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



def create_cybersecurity_scheduler_runtime(
    workflow_service=None,
) -> CybersecuritySchedulerRuntime:
    """
    Create configured cybersecurity scheduler runtime.

    Dependencies can be injected for:
    - testing;
    - production providers;
    - future integrations.
    """



    #
    # Default workflow composition
    #

    if workflow_service is None:


        email_service = (
            CybersecurityEmailService(
                recipient=(
                    "davdbarbero1999@gmail.com"
                ),
            )
        )



        workflow_service = (
            CybersecuritySchedulerWorkflow(

                email_service=email_service,

            )
        )



    #
    # APScheduler infrastructure
    #

    scheduler = AsyncIOScheduler(

        timezone=SCHEDULER_TIMEZONE,

    )



    #
    # Infrastructure adapter boundary
    #

    adapter = (
        CybersecurityAPSchedulerAdapter(

            scheduler=scheduler,

            workflow_service=workflow_service,

        )
    )



    #
    # Runtime boundary
    #

    runtime = (
        CybersecuritySchedulerRuntime(

            scheduler_adapter=adapter,

        )
    )



    return runtime

