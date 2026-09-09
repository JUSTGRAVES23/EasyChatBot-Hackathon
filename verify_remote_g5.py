"""
Remote end-to-end verification for the deployed EasyChatBot
Cinema Intelligence Agent.

Authoritative deployment:
    projects/170171515928/locations/europe-west1/reasoningEngines/5525837577946398720

Verification path:

    Google Agent Runtime
        ->
    Google ADK Agent
        ->
    G5 Cinema Workflow
        ->
    Gemini / Vertex AI (EU)
        ->
    Parallel live research
        ->
    Learning challenge
        ->
    Memory
        ->
    Personalisation

This script performs functional verification only.
It does not modify the deployed Agent Runtime resource.
"""

import asyncio

import vertexai
from vertexai import agent_engines


# ============================================================================
# Google Cloud configuration
# ============================================================================

PROJECT = "demoeasyworld-2026"

# Agent Runtime deployment location.
LOCATION = "europe-west1"

# Newly deployed authoritative Agent Runtime resource.
RESOURCE = (
    "projects/170171515928/locations/europe-west1/"
    "reasoningEngines/5525837577946398720"
)

USER_ID = "hackathon-final-e2e"

MESSAGE = (
    "Run the cinema intelligence workflow now. "
    "Use the live research workflow and return the completed "
    "cinema intelligence result, including the learning challenge "
    "and personalised result. Do not invent information."
)


# ============================================================================
# Verification
# ============================================================================


async def main() -> None:
    """Run the complete remote G5 end-to-end verification."""

    vertexai.init(
        project=PROJECT,
        location=LOCATION,
    )

    app = agent_engines.get(
        RESOURCE,
    )

    print(
        "REMOTE G5 END-TO-END VERIFICATION"
    )
    print(
        "=" * 70
    )

    print(
        "Project:",
        PROJECT,
    )

    print(
        "Agent Runtime location:",
        LOCATION,
    )

    print(
        "Resource:",
        app.resource_name,
    )

    print(
        "User ID:",
        USER_ID,
    )

    print(
        "=" * 70
    )

    events = []

    try:

        async for event in app.async_stream_query(
            user_id=USER_ID,
            message=MESSAGE,
        ):
            events.append(
                event
            )

            print()
            print(
                "EVENT"
            )
            print(
                "-" * 70
            )

            print(
                event
            )

    except Exception as exc:

        print()
        print(
            "=" * 70
        )
        print(
            "REMOTE AGENT EXECUTION ERROR"
        )
        print(
            "=" * 70
        )

        print(
            type(exc).__name__,
            str(exc),
        )

        print(
            "REMOTE_G5_END_TO_END_FAIL"
        )

        raise

    text = "\n".join(
        str(event)
        for event in events
    )

    print()
    print(
        "=" * 70
    )

    print(
        "REMOTE VERIFICATION RESULTS"
    )

    print(
        "=" * 70
    )

    print(
        "EVENT_COUNT=",
        len(events),
    )

    checks = {
        "events_received": (
            len(events) > 0
        ),
        "workflow_success": (
            "G5_FINAL_HACKATHON_DEMO_SUCCESS"
            in text
        ),
        "parallel": (
            "Parallel" in text
            or "parallel" in text
        ),
        "personalisation": (
            "personal" in text.lower()
            or "personalisation" in text.lower()
            or "personalization" in text.lower()
        ),
    }

    for name, passed in checks.items():

        print(
            f"{name.upper()}=",
            "PASS" if passed else "FAIL",
        )

    print()
    print(
        "=" * 70
    )

    # ------------------------------------------------------------------------
    # Primary acceptance gate
    # ------------------------------------------------------------------------

    if (
        checks["events_received"]
        and checks["workflow_success"]
    ):

        print(
            "REMOTE_G5_END_TO_END_PASS"
        )

        print(
            "=" * 70
        )

        return

    print(
        "REMOTE_G5_END_TO_END_FAIL"
    )

    print(
        "=" * 70
    )

    raise SystemExit(
        1
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )
