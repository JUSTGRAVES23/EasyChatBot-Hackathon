from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class AgentExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    agent_id: str
    capability: str
    instruction: str
    context: Any
    metadata: dict[str, Any] = {}
