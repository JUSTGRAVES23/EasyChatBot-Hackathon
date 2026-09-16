import pytest

from cybersecurity.scheduler.cybersecurity_schedule_configuration import (
    CybersecurityScheduleConfiguration,
)


from cybersecurity.scheduler.cybersecurity_job_registry import (
    CybersecurityJobRegistry,
)


def test_scheduler_configuration():

    config = CybersecurityScheduleConfiguration.get_configuration()

    assert config["daily"] == "08:00"
    assert config["weekly"] == "MONDAY 08:00"
    assert config["critical"] == "IMMEDIATE"



def test_job_registry():

    registry = CybersecurityJobRegistry()

    registry.register(
        "daily_security_report",
        "08:00",
    )

    assert len(registry.list_jobs()) == 1


