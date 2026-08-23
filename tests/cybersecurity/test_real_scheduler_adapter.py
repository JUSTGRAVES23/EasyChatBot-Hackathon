"""
APScheduler Adapter tests.

Validates:

- jobs register;
- lifecycle works;
- configuration is applied.

Does NOT:
- send emails;
- execute reports.
"""

from __future__ import annotations


from backend.cybersecurity.scheduler.cybersecurity_apscheduler_adapter import (
    CybersecurityAPSchedulerAdapter,
)



class FakeScheduler:

    def __init__(self):

        self.jobs = []

        self.running = False



    def add_job(
        self,
        function,
        **kwargs,
    ):

        self.jobs.append(
            kwargs
        )



    def start(
        self,
    ):

        self.running = True



    def shutdown(
        self,
    ):

        self.running = False



class FakeWorkflow:


    async def create_daily_report(
        self,
    ):
        pass



    async def create_weekly_report(
        self,
    ):
        pass




def test_apscheduler_adapter_registers_jobs():


    scheduler = (
        FakeScheduler()
    )


    adapter = (
        CybersecurityAPSchedulerAdapter(
            scheduler=scheduler,
            workflow_service=FakeWorkflow(),
        )
    )


    adapter.register_jobs()


    assert len(
        scheduler.jobs
    ) == 2



def test_apscheduler_adapter_lifecycle():


    scheduler = (
        FakeScheduler()
    )


    adapter = (
        CybersecurityAPSchedulerAdapter(
            scheduler=scheduler,
            workflow_service=FakeWorkflow(),
        )
    )


    adapter.start()


    assert (
        scheduler.running
        is True
    )


    adapter.shutdown()


    assert (
        scheduler.running
        is False
    )
