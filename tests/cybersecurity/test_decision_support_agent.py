import pytest


from backend.cybersecurity.decision_support.agent.agent import (
    CybersecurityDecisionSupportAgent,
)



@pytest.mark.asyncio
async def test_agent_creates_decision_brief():


    agent = (
        CybersecurityDecisionSupportAgent()
    )


    result = await agent.analyse(

        {

            "signals": [

                {

                    "signal_id":
                    "test-001",

                    "title":
                    "AI prompt injection attempt",

                    "severity":
                    "high",

                    "category":
                    "threat",

                    "confidence":
                    0.96,

                    "affected_area":
                    "AI layer",

                }

            ]

        }

    )


    assert (
        result.overall_priority
        ==
        "HIGH REVIEW REQUIRED"
    )


    assert len(
        result.high_priority_items
    ) == 1
