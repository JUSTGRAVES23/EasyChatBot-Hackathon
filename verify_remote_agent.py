"""Remote verification for the deployed EasyChatBot Cinema Intelligence Agent."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import vertexai
from vertexai import agent_engines


PROJECT_ID = "demoeasyworld-2026"
LOCATION = "eu"

AGENT_RESOURCE = (
    "projects/170171515928/"
    "locations/eu/"
    "reasoningEngines/REPLACE_WITH_NEW_EU_RESOURCE_ID"
)

USER_ID = "hackathon-remote-smoke-test"

TEST_MESSAGE = (
    "Run the cinema intelligence workflow and give me the "
    "current AI developments relevant to filmmakers. "
    "Use the live research workflow and report the result clearly."
)


def extract_text_from_event(event: Any) -> list[str]:
    """Extract model text from a Google ADK event dictionary."""

    if not isinstance(event, dict):
        return []

    content = event.get("content")

    if not isinstance(content, dict):
        return []

    parts = content.get("parts", [])

    if not isinstance(parts, list):
        return []

    texts: list[str] = []

    for part in parts:
        if not isinstance(part, dict):
            continue

        text = part.get("text")

        if isinstance(text, str) and text.strip():
            texts.append(text.strip())

    return texts


def extract_event_diagnostics(event: Any) -> dict[str, Any]:
    """Extract safe diagnostic information from an event."""

    if not isinstance(event, dict):
        return {
            "event_type": type(event).__name__,
        }

    diagnostics: dict[str, Any] = {
        "event_type": "dict",
        "id": event.get("id"),
        "author": event.get("author"),
        "invocation_id": event.get("invocation_id"),
        "timestamp": event.get("timestamp"),
    }

    content = event.get("content")

    if isinstance(content, dict):
        diagnostics["role"] = content.get("role")

        parts = content.get("parts")

        if isinstance(parts, list):
            diagnostics["part_count"] = len(parts)

            part_types: list[list[str]] = []

            for part in parts:
                if isinstance(part, dict):
                    part_types.append(sorted(part.keys()))

            diagnostics["part_keys"] = part_types

    actions = event.get("actions")

    if isinstance(actions, dict):
        diagnostics["action_keys"] = sorted(actions.keys())

    return diagnostics


def extract_error_from_event(event: Any) -> str | None:
    """Extract a useful remote error from an Agent Runtime event."""

    if not isinstance(event, dict):
        return None

    error = event.get("error")

    if error:
        if isinstance(error, dict):
            return json.dumps(
                error,
                ensure_ascii=False,
                default=str,
            )
        return str(error)

    for key in ("errorMessage", "error_message", "message"):
        value = event.get(key)

        if isinstance(value, str) and value.strip():
            if "error" in value.lower() or "not_found" in value.lower():
                return value.strip()

    return None


def validate_configuration() -> None:
    """Fail early if the deployed EU resource ID has not been supplied."""

    if "REPLACE_WITH_NEW_EU_RESOURCE_ID" in AGENT_RESOURCE:
        raise RuntimeError(
            "AGENT_RESOURCE still contains the placeholder. "
            "Replace REPLACE_WITH_NEW_EU_RESOURCE_ID with the new "
            "Agent Runtime resource ID created in the eu location."
        )


async def main() -> None:
    validate_configuration()

    print()
    print("=" * 70)
    print("REMOTE AGENT RUNTIME SMOKE TEST")
    print("=" * 70)

    print()
    print(f"Project:  {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Resource: {AGENT_RESOURCE}")
    print(f"User:     {USER_ID}")

    print()
    print("Initialising Vertex AI...")

    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
    )

    print("Loading remote Agent Runtime resource...")

    remote_agent = agent_engines.get(
        AGENT_RESOURCE
    )

    print()
    print("Remote resource loaded:")
    print(f"  {remote_agent.resource_name}")

    if remote_agent.resource_name != AGENT_RESOURCE:
        raise RuntimeError(
            "Loaded Agent Runtime resource does not match the "
            "configured resource."
        )

    print()
    print("Supported remote operations:")

    try:
        schemas = remote_agent.operation_schemas()

        if isinstance(schemas, list):
            for schema in schemas:
                if isinstance(schema, dict):
                    print(
                        f"  - {schema.get('name', '<unnamed>')} "
                        f"[{schema.get('api_mode', '')}]"
                    )
                else:
                    print(f"  - {schema}")
        elif isinstance(schemas, dict):
            for name in schemas:
                print(f"  - {name}")
        else:
            print(f"  {schemas}")

    except Exception as exc:
        print(
            f"  WARNING: operation schema inspection failed: {exc}"
        )

    print()
    print("Sending smoke-test request:")
    print(f"  {TEST_MESSAGE}")

    print()
    print("Waiting for remote agent response...")
    print("-" * 70)

    final_text: list[str] = []
    event_count = 0
    error_events: list[str] = []

    try:
        async for event in remote_agent.async_stream_query(
            user_id=USER_ID,
            message=TEST_MESSAGE,
        ):
            event_count += 1

            diagnostics = extract_event_diagnostics(event)
            remote_error = extract_error_from_event(event)

            print()
            print(
                f"[event {event_count}] "
                f"{diagnostics.get('event_type')}"
            )

            print(
                "  "
                + json.dumps(
                    diagnostics,
                    ensure_ascii=False,
                    default=str,
                )
            )

            if remote_error:
                error_events.append(remote_error)

                print()
                print("  REMOTE ERROR:")
                print("  " + remote_error.replace("\n", "\n  "))

            texts = extract_text_from_event(event)

            for text in texts:
                final_text.append(text)

                print()
                print("  TEXT:")
                print("  " + text.replace("\n", "\n  "))

    except Exception as exc:
        print()
        print("=" * 70)
        print("REMOTE AGENT EXECUTION EXCEPTION")
        print("=" * 70)
        print(f"{type(exc).__name__}: {exc}")
        raise

    print()
    print("-" * 70)

    response = "\n".join(final_text).strip()

    print()
    print("REMOTE RESPONSE:")
    print(response if response else "<NO TEXT EVENT>")

    print()
    print(f"Events received: {event_count}")
    print(f"Text events:     {len(final_text)}")
    print(f"Remote errors:   {len(error_events)}")

    if error_events:
        raise RuntimeError(
            "Remote Agent Runtime returned an explicit error event: "
            + " | ".join(error_events)
        )

    if event_count == 0:
        raise RuntimeError(
            "Remote agent returned zero events."
        )

    if not response:
        raise RuntimeError(
            "Remote agent returned events, but no textual model "
            "response was found. Review the event diagnostics above."
        )

    print()
    print("=" * 70)
    print("REMOTE_AGENT_RUNTIME_SMOKE_TEST_PASS")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
