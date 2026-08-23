"""
Scheduler workflow execution tests.
"""

from __future__ import annotations


import pytest


from backend.cybersecurity.scheduler.cybersecurity_scheduler_workflow import (
    CybersecuritySchedulerWorkflow,
)



@pytest.mark.asyncio
async def test_daily_workflow_execution():


    workflow = (
        CybersecuritySchedulerWorkflow()
    )


    result = await (
        workflow.create_daily_report()
    )


    assert (
        result["type"]
        == "daily"
    )



@pytest.mark.asyncio
async def test_weekly_workflow_execution():


    workflow = (
        CybersecuritySchedulerWorkflow()
    )


    result = await (
        workflow.create_weekly_report()
    )


    assert (
        result["type"]
        == "weekly"
    )



@pytest.mark.asyncio
async def test_critical_workflow_execution():


    workflow = (
        CybersecuritySchedulerWorkflow()
    )


    result = await (
        workflow.create_critical_alert(
            {
                "severity": "critical"
            }
        )
    )


    assert (
        result["type"]
        == "critical"
    )
