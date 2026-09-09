"""End-to-end local execution test for the ADK cinema agent."""

from __future__ import annotations

import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from adk_cinema.agent import root_agent


APP_NAME = "easychatbot_cinema"
USER_ID = "hackathon-test-user"
SESSION_ID = "hackathon-test-session"


async def main() -> None:
    print("=" * 60)
    print("ADK CINEMA AGENT — EXECUTION TEST")
    print("=" * 60)

    session_service = InMemorySessionService()

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    "Run the cinema intelligence workflow and give me "
                    "the resulting current intelligence."
                )
            )
        ],
    )

    tool_executed = False
    final_response = None

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=message,
    ):
        print(f"Event: {type(event).__name__}")

        if getattr(event, "content", None):
            content = event.content

            for part in getattr(content, "parts", []) or []:
                text = getattr(part, "text", None)

                if text:
                    print(f"Agent: {text[:500]}")

                function_call = getattr(part, "function_call", None)

                if function_call:
                    print(
                        f"Tool call: "
                        f"{getattr(function_call, 'name', 'unknown')}"
                    )

                    if (
                        getattr(function_call, "name", None)
                        == "run_g5_cinema_workflow"
                    ):
                        tool_executed = True

        if getattr(event, "is_final_response", lambda: False)():
            final_response = event

    print("\n========== EXECUTION RESULT ==========")
    print(f"Tool executed: {tool_executed}")
    print(f"Final response received: {final_response is not None}")

    assert tool_executed, (
        "ADK did not invoke run_g5_cinema_workflow."
    )

    assert final_response is not None, (
        "ADK did not produce a final response."
    )

    print("\nADK_CINEMA_AGENT_EXECUTION_PASS")


if __name__ == "__main__":
    asyncio.run(main())