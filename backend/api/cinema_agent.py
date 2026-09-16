"""FastAPI boundary for the deployed Google Agentic Cinema agent."""

from __future__ import annotations

import json
import os
from typing import Any

import google.auth
import requests
from google.auth.transport.requests import Request
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api", tags=["cinema"])


DEFAULT_PROJECT_ID = "demoeasyworld-2026"
DEFAULT_LOCATION = "europe-west1"
DEFAULT_REASONING_ENGINE_ID = "5525837577946398720"

PROJECT_ID = os.getenv(
    "EASYCHATBOT_AGENT_PROJECT",
    DEFAULT_PROJECT_ID,
).strip()

LOCATION = os.getenv(
    "EASYCHATBOT_AGENT_LOCATION",
    DEFAULT_LOCATION,
).strip()

REASONING_ENGINE_ID = os.getenv(
    "EASYCHATBOT_AGENT_ENGINE_ID",
    DEFAULT_REASONING_ENGINE_ID,
).strip()


AGENT_RESOURCE_NAME = (
    f"projects/{PROJECT_ID}/locations/{LOCATION}/"
    f"reasoningEngines/{REASONING_ENGINE_ID}"
)

AGENT_STREAM_URL = (
    f"https://{LOCATION}-aiplatform.googleapis.com/v1/"
    f"{AGENT_RESOURCE_NAME}:streamQuery?alt=sse"
)


class CinemaRequest(BaseModel):
    message: str = Field(min_length=1)
    userId: str = Field(default="hackathon-user", min_length=1)
    language: str = Field(default="French", min_length=1)
    learnerLevel: str = Field(default="B2", min_length=1)


class CinemaActionRequest(BaseModel):
    action: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


def _get_access_token() -> str:
    """Obtain an ADC access token for Google Cloud."""
    credentials, _ = google.auth.default()
    credentials.refresh(Request())

    if not credentials.token:
        raise RuntimeError("Google Cloud credentials did not provide an access token.")

    return credentials.token


def _parse_sse_response(response: requests.Response) -> list[dict[str, Any]]:
    """Parse Agent Runtime SSE/JSON event lines safely."""
    events: list[dict[str, Any]] = []

    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue

        line = raw_line.strip()

        # Standard SSE payload.
        if line.startswith("data:"):
            line = line[5:].strip()

        if not line:
            continue

        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue

        if isinstance(value, dict):
            events.append(value)

    return events


def _extract_event_text(events: list[dict[str, Any]]) -> str:
    """Extract the final textual response from Agent Runtime events."""
    text_parts: list[str] = []

    for event in events:
        content = event.get("content")

        if not isinstance(content, dict):
            continue

        parts = content.get("parts")

        if not isinstance(parts, list):
            continue

        for part in parts:
            if not isinstance(part, dict):
                continue

            text = part.get("text")

            if isinstance(text, str) and text.strip():
                text_parts.append(text.strip())

    return "\n\n".join(text_parts)


def _extract_tool_result(
    events: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Extract the G5 function response returned by the ADK tool."""
    for event in events:
        content = event.get("content")

        if not isinstance(content, dict):
            continue

        parts = content.get("parts")

        if not isinstance(parts, list):
            continue

        for part in parts:
            if not isinstance(part, dict):
                continue

            function_response = part.get("function_response")

            if not isinstance(function_response, dict):
                continue

            response = function_response.get("response")

            if isinstance(response, dict):
                return response

    return None


def _invoke_agent(
    *,
    message: str,
    user_id: str,
) -> dict[str, Any]:
    """Invoke the deployed ADK agent through Agent Runtime."""
    token = _get_access_token()

    payload = {
        "class_method": "async_stream_query",
        "input": {
            "user_id": user_id,
            "message": message,
        },
    }

    try:
        response = requests.post(
            AGENT_STREAM_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            stream=True,
            timeout=180,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Unable to connect to Google Agent Runtime: {exc}"
        ) from exc

    if response.status_code >= 400:
        body = response.text[:2000]

        raise RuntimeError(
            f"Google Agent Runtime returned HTTP "
            f"{response.status_code}: {body}"
        )

    events = _parse_sse_response(response)

    if not events:
        raise RuntimeError(
            "Google Agent Runtime returned no usable events."
        )

    final_text = _extract_event_text(events)
    tool_result = _extract_tool_result(events)

    return {
        "events": events,
        "text": final_text,
        "tool_result": tool_result,
    }


def _build_cinema_result(
    *,
    agent_response: dict[str, Any],
    request: CinemaRequest,
) -> dict[str, Any]:
    """Convert Agent Runtime output into the stable Cinema frontend contract."""
    tool_result = agent_response.get("tool_result")

    result_text = agent_response.get("text", "")

    if not isinstance(result_text, str):
        result_text = ""

    success = False

    if isinstance(tool_result, dict):
        success = bool(tool_result.get("success"))

    raw_result = ""

    if isinstance(tool_result, dict):
        candidate = tool_result.get("result")

        if isinstance(candidate, str):
            raw_result = candidate

    return {
        "success": success,
        "result": result_text,
        "intelligence": {
            "summary": result_text,
        },
        "summary": result_text,
        "sources": [],
        "learning_challenge": None,
        "personalisation": {
            "language": request.language,
            "learnerLevel": request.learnerLevel,
        },
        "raw_agent_response": raw_result,
        "agent": "easychatbot_cinema_agent",
        "reasoning_engine": AGENT_RESOURCE_NAME,
    }


@router.post("/cinema")
def run_cinema(request: CinemaRequest) -> dict[str, Any]:
    """Run the deployed Agentic Cinema workflow."""
    enriched_message = (
        f"{request.message}\n\n"
        f"Learner language: {request.language}\n"
        f"Learner level: {request.learnerLevel}\n"
        "Return the result clearly for the Cinema interface."
    )

    try:
        agent_response = _invoke_agent(
            message=enriched_message,
            user_id=request.userId,
        )

        return _build_cinema_result(
            agent_response=agent_response,
            request=request,
        )

    except Exception as exc:
        # Keep infrastructure details out of the client response.
        print(f"[cinema] Agent Runtime invocation failed: {exc}")

        raise HTTPException(
            status_code=502,
            detail="Cinema Agent Runtime is currently unavailable.",
        ) from exc


@router.post("/cinema/action")
def run_cinema_action(
    request: CinemaActionRequest,
) -> dict[str, Any]:
    """Handle controlled Cinema actions."""
    action = request.action.strip().lower()

    if action == "save":
        return {
            "success": True,
            "saved": False,
            "message": "Save persistence is not enabled in the Cinema demo.",
        }

    if action == "challenge":
        question = request.payload.get("question", "")
        answer = request.payload.get("answer", "")

        if not isinstance(question, str):
            question = str(question)

        if not isinstance(answer, str):
            answer = str(answer)

        if not answer.strip():
            return {
                "success": False,
                "message": "Please provide an answer before submitting.",
            }

        prompt = (
            "Evaluate this French learning challenge answer.\n\n"
            f"Question:\n{question}\n\n"
            f"Learner answer:\n{answer}\n\n"
            "Give concise feedback appropriate for a B2 learner."
        )

        try:
            agent_response = _invoke_agent(
                message=prompt,
                user_id="hackathon-challenge",
            )

            return {
                "success": True,
                "feedback": agent_response.get("text", ""),
            }

        except Exception as exc:
            print(f"[cinema] Challenge invocation failed: {exc}")

            raise HTTPException(
                status_code=502,
                detail="Cinema Agent Runtime is currently unavailable.",
            ) from exc

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported Cinema action: {request.action}",
    )