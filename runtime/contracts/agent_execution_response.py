from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentExecutionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    execution_id: str
    agent_id: str
    capability: str
    content: str = ""
    structured_output: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
