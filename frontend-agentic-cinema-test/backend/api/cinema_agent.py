"""FastAPI boundary for the deployed Google Agent Runtime cinema agent."""
from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/cinema", tags=["agentic-cinema"])

DEFAULT_RESOURCE = (
    "projects/170171515928/locations/europe-west1/"
    "reasoningEngines/5525837577946398720"
)

class CinemaRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    user_id: str = Field(default="hackathon-judge", min_length=1, max_length=200)
    language: str = Field(default="French", max_length=40)
    learner_level: str = Field(default="B2", max_length=20)

class CinemaAction(BaseModel):
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)


def _resource() -> str:
    return os.getenv("EASYCHATBOT_CINEMA_AGENT_RESOURCE", DEFAULT_RESOURCE).strip()

async def _query_agent(user_id: str, message: str) -> list[str]:
    try:
        from vertexai import agent_engines
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Google Vertex Agent Runtime SDK is unavailable.") from exc

    try:
        remote_agent = agent_engines.get(_resource())
        texts: list[str] = []
        async for event in remote_agent.async_stream_query(user_id=user_id, message=message):
            if not isinstance(event, dict):
                continue
            content = event.get("content")
            if not isinstance(content, dict):
                continue
            for part in content.get("parts", []):
                if isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"].strip():
                    texts.append(part["text"].strip())
        return texts
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Cinema Agent Runtime request failed: {exc}") from exc

@router.post("")
async def cinema(request: CinemaRequest) -> dict[str, Any]:
    texts = await _query_agent(
        request.user_id,
        request.message.strip(),
    )
    if not texts:
        raise HTTPException(status_code=502, detail="Cinema agent returned no text output.")
    return {"success": True, "result": "\n\n".join(texts), "intelligence": "\n\n".join(texts)}

@router.post("/action")
async def cinema_action(action: CinemaAction) -> dict[str, Any]:
    if action.action != "challenge":
        return {"success": False, "configured": False, "error": "Only the live challenge action is exposed by this adapter."}
    question = str(action.payload.get("question", ""))
    challenge = action.payload.get("challenge")
    answer = str(action.payload.get("answer", ""))
    if not answer.strip():
        return {"success": False, "configured": True, "error": "answer is required."}
    prompt = (
        "Evaluate this French learner answer against the provided cinema learning challenge. "
        "Give concise feedback, a score from 0 to 100, and one correction.\n"
        f"Question: {question}\nChallenge: {challenge}\nAnswer: {answer}"
    )
    texts = await _query_agent("hackathon-judge-challenge", prompt)
    return {"success": bool(texts), "result": "\n\n".join(texts)}
