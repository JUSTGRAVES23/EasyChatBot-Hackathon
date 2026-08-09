"""
EasyChatBot Parallel Search Demo.

Demonstrates:

User request
      |
Research Agent
      |
Parallel Provider
      |
Parallel API
      |
Response

This script uses the real Parallel API.
"""

import asyncio

from backend.agents.research_agent import ResearchAgent
from backend.runtime.context.execution_context import ExecutionContext


async def main():

    agent = ResearchAgent()

    context = ExecutionContext(
        user_id="demo-user",
        request=(
            "What are the latest "
            "artificial intelligence news?"
        ),
    )

    result = await agent.execute(
        context
    )

    print("=" * 60)

    print(
        "EasyChatBot Research Agent Demo"
    )

    print("=" * 60)

    print()

    print(
        "Agent:",
        result.agent_id
    )

    print()

    print(
        "Success:",
        result.success
    )

    print()

    print(
        "Result:"
    )

    print(
        result.output
    )


if __name__ == "__main__":

    asyncio.run(main())