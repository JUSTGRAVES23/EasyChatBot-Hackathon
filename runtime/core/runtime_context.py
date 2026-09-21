"""Canonical governed AI Runtime execution context.

This context is the runtime state envelope shared across governed execution
stages. It is intentionally provider-neutral and does not perform I/O.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuntimeContext(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    execution_id: str
    pipeline_name: str = ""
    capability_id: str = ""
    capability_name: str = ""
    work_item: Any = None

    system_prompt: str = ""
    rendered_prompt: str = ""

    provider_id: str = ""
    model_name: str = ""

    raw_response: Any = None
    parsed_response: Any = None

    memory: Any = None
    artifacts: list[Any] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    events: list[Any] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def add_event(self, event: Any) -> None:
        self.events.append(event)

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def add_error(self, error: str) -> None:
        self.errors.append(error)
