import asyncio

import vertexai
from vertexai import agent_engines


PROJECT = "demoeasyworld-2026"
LOCATION = "europe-west1"
RESOURCE = (
    "projects/170171515928/locations/europe-west1/"
    "reasoningEngines/6151274976197476352"
)


async def main():
    vertexai.init(
        project=PROJECT,
        location=LOCATION,
    )

    app = agent_engines.get(RESOURCE)

    print("REMOTE AGENT VERIFICATION")
    print("=" * 60)
    print("Resource:", app.resource_name)
    print("Display:", app.display_name)

    print("\nStarting remote query...")

    events = []

    try:
        async for event in app.async_stream_query(
            user_id="hackathon-remote-verification",
            message=(
                "Run the cinema intelligence workflow and return "
                "the result. Confirm whether the workflow succeeded."
            ),
        ):
            events.append(event)

            print("\nEVENT")
            print("-" * 60)
            print(event)

    except Exception as exc:
        print("\nREMOTE EXECUTION FAILED")
        print(type(exc).__name__)
        print(str(exc))
        raise

    print("\n" + "=" * 60)
    print("EVENT_COUNT=", len(events))

    text = "\n".join(
        str(event)
        for event in events
    )

    if "404_NOT_FOUND" in text or "NOT_FOUND" in text:
        print("REMOTE_AGENT_RUNTIME_SMOKE_TEST_FAIL_MODEL_NOT_FOUND")
        raise SystemExit(1)

    if "G5_FINAL_HACKATHON_DEMO_SUCCESS" in text:
        print("REMOTE_AGENT_RUNTIME_SMOKE_TEST_PASS")
    else:
        print("REMOTE_AGENT_RUNTIME_RESPONSE_RECEIVED")


if __name__ == "__main__":
    asyncio.run(main())
