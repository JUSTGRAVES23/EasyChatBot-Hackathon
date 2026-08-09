from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from typing import Any


@dataclass(frozen=True)
class ExecutionContext:
    """
    Runtime execution context shared with agents.

    Responsibilities:
    - identify an execution
    - carry user request information
    - provide runtime metadata

    Does not:
    - execute providers
    - manage memory
    - modify systems
    """

    user_id: str
    request: str

    execution_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )