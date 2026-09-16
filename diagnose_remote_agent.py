"""Deep diagnostic for the deployed Google Agent Runtime ADK agent."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import google.auth
import google.auth.transport.requests
import requests


PROJECT_ID = "demoeasyworld-2026"
PROJECT_NUMBER = "170171515928"
LOCATION = "europe-west1"

RESOURCE_ID = "1490612311822434304"

RESOURCE_NAME = (
    f"projects/{PROJECT_NUMBER}/"
    f"locations/{LOCATION}/"
    f"reasoningEngines/{RESOURCE_ID}"
)

USER_ID = "hackathon-deep-diagnostic"

BASE_URL = (
    f"https://{LOCATION}-aiplatform.googleapis.com/v1/"
    f"projects/{PROJECT_ID}/locations/{LOCATION}/"
    f"reasoningEngines/{RESOURCE_ID}"
)

QUERY_URL = f"{BASE_URL}:query"
STREAM_URL = f"{BASE_URL}:streamQuery?alt=sse"

TEST_MESSAGE = (
    "Run the cinema intelligence workflow. "
    "Return a concise result about current AI developments "
    "relevant to filmmakers."
)


def get_access_token() -> str:
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    auth_request = google.auth.transport.requests.Request()
    credentials.refresh(auth_request)

    if not credentials.token:
        raise RuntimeError("Google credentials produced no access token.")

    return credentials.token


def headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
    }


def print_response(label: str, response: requests.Response) -> None:
    print()
    print("=" * 80)
    print(label)
    print("=" * 80)

    print(f"HTTP status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Content-Length: {response.headers.get('content-length')}")

    print()
    print("Headers:")

    for key, value in response.headers.items():
        if key.lower() in {
            "authorization",
            "cookie",
            "set-cookie",
        }:
            continue

        print(f"  {key}: {value}")

    print()
    print("Body:")

    text = response.text

    if not text:
        print("<EMPTY BODY>")
        return

    print(text[:20000])


def create_session() -> str:
    print()
    print("=" * 80)
    print("STEP 1 — CREATE MANAGED ADK SESSION")
    print("=" * 80)

    payload = {
        "class_method": "async_create_session",
        "input": {
            "user_id": USER_ID,
        },
    }

    response = requests.post(
        QUERY_URL,
        headers=headers(),
        json=payload,
        timeout=120,
    )

    print_response(
        "CREATE SESSION RESPONSE",
        response,
    )

    response.raise_for_status()

    data: dict[str, Any] = response.json()

    output = data.get("output")

    if not isinstance(output, dict):
        raise RuntimeError(
            "Session creation succeeded HTTP-wise but returned no "
            "'output' object."
        )

    session_id = output.get("id")

    if not isinstance(session_id, str) or not session_id:
        raise RuntimeError(
            "Session creation returned no valid session ID."
        )

    print()
    print(f"CREATED SESSION ID: {session_id}")

    return session_id


def run_stream_query(session_id: str) -> None:
    print()
    print("=" * 80)
    print("STEP 2 — DIRECT REST STREAM QUERY")
    print("=" * 80)

    payload = {
        "class_method": "async_stream_query",
        "input": {
            "user_id": USER_ID,
            "session_id": session_id,
            "message": TEST_MESSAGE,
        },
    }

    print()
    print("Request URL:")
    print(STREAM_URL)

    print()
    print("Request payload:")
    print(
        json.dumps(
            payload,
            indent=2,
        )
    )

    print()
    print("Opening SSE stream...")

    with requests.post(
        STREAM_URL,
        headers=headers(),
        json=payload,
        stream=True,
        timeout=300,
    ) as response:

        print_response(
            "STREAM INITIAL RESPONSE",
            response,
        )

        response.raise_for_status()

        print()
        print("=" * 80)
        print("SSE EVENTS")
        print("=" * 80)

        event_count = 0
        meaningful_count = 0

        for raw_line in response.iter_lines(
            decode_unicode=True
        ):
            if raw_line is None:
                continue

            line = raw_line.strip()

            if not line:
                continue

            event_count += 1

            print()
            print(f"[SSE {event_count}]")
            print(line)

            if line.startswith("data:"):
                data_text = line[5:].strip()

                if not data_text:
                    continue

                try:
                    parsed = json.loads(data_text)

                    if parsed:
                        meaningful_count += 1

                        print()
                        print("PARSED EVENT:")
                        print(
                            json.dumps(
                                parsed,
                                indent=2,
                                ensure_ascii=False,
                                default=str,
                            )[:20000]
                        )

                except json.JSONDecodeError:
                    print(
                        "Non-JSON SSE payload."
                    )

        print()
        print("=" * 80)
        print("STREAM SUMMARY")
        print("=" * 80)

        print(f"SSE lines:       {event_count}")
        print(f"Meaningful JSON: {meaningful_count}")

        if meaningful_count == 0:
            raise RuntimeError(
                "Agent Runtime stream returned no meaningful JSON events."
            )


def main() -> None:
    print()
    print("=" * 80)
    print("GOOGLE AGENT RUNTIME DEEP DIAGNOSTIC")
    print("=" * 80)

    print()
    print(f"Project:       {PROJECT_ID}")
    print(f"Project number:{PROJECT_NUMBER}")
    print(f"Location:      {LOCATION}")
    print(f"Resource:      {RESOURCE_NAME}")
    print(f"User:          {USER_ID}")

    print()
    print("Authenticating with Application Default Credentials...")

    token = get_access_token()

    print(
        f"Authentication PASS — token acquired "
        f"({len(token)} characters)"
    )

    session_id = create_session()

    run_stream_query(session_id)

    print()
    print("=" * 80)
    print("REMOTE_AGENT_DIRECT_REST_DIAGNOSTIC_PASS")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print()
        print("=" * 80)
        print("REMOTE_AGENT_DIRECT_REST_DIAGNOSTIC_FAILED")
        print("=" * 80)
        print(f"{type(exc).__name__}: {exc}")
        sys.exit(1)