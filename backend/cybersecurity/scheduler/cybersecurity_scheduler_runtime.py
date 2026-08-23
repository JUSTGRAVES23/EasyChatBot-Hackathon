"""
Cybersecurity Scheduler Runtime.

Lifecycle manager for cybersecurity scheduling.

Responsibilities:
- start scheduler;
- register jobs;
- stop scheduler;
- expose runtime state.

Does NOT:
- execute reports;
- send emails;
- make security decisions;
- perform remediation.
"""

from __future__ import annotations


from backend.cybersecurity.scheduler.cybersecurity_job_registry import (
    CybersecurityJobRegistry,
)



class CybersecuritySchedulerRuntime:
    """
    Scheduler lifecycle boundary.

    Supports:

    - registry based execution/testing;
    - production scheduler adapter.

    Architecture:

        FastAPI lifespan
              |
              v
    CybersecuritySchedulerRuntime
              |
              +----------------+
              |                |
              v                v

        Job Registry     Scheduler Adapter

          (tests)          (production)

    """



    def __init__(
        self,
        scheduler_adapter=None,
        job_registry: CybersecurityJobRegistry | None = None,
    ) -> None:
        """
        Initialize scheduler runtime.
        """


        self.scheduler_adapter = (
            scheduler_adapter
        )


        self.job_registry = (
            job_registry
            or CybersecurityJobRegistry()
        )


        self._started = False



    async def start(
        self,
    ) -> None:
        """
        Start scheduler runtime.

        Registers scheduled cybersecurity workflows.
        """


        if self.scheduler_adapter is not None:

            #
            # Production scheduler boundary.
            #
            # Example:
            # APScheduler adapter
            #

            self.scheduler_adapter.register_jobs()

            self.scheduler_adapter.start()


        else:

            #
            # Registry mode.
            #
            # Used for testing and controlled execution.
            #

            self.job_registry.register(

                name=(
                    "cybersecurity_daily_report"
                ),

                schedule=(
                    "daily_08:00"
                ),

            )


            self.job_registry.register(

                name=(
                    "cybersecurity_weekly_report"
                ),

                schedule=(
                    "weekly_monday_08:00"
                ),

            )


            self.job_registry.register(

                name=(
                    "cybersecurity_critical_alert"
                ),

                schedule=(
                    "event_immediate"
                ),

            )



        self._started = True



    async def stop(
        self,
    ) -> None:
        """
        Stop scheduler runtime.
        """


        if self.scheduler_adapter is not None:

            self.scheduler_adapter.shutdown()



        self._started = False



    def status(
        self,
    ) -> dict:
        """
        Return scheduler runtime status.

        Provides backward-compatible fields:

        - jobs
        - registered_jobs
        """


        jobs = (
            self.job_registry.list_jobs()
        )



        return {

            "started":
                self._started,


            "adapter_enabled":
                self.scheduler_adapter is not None,


            #
            # Existing test contract
            #
            "jobs":
                jobs,


            #
            # Extended API contract
            #
            "registered_jobs":
                jobs,

        }
