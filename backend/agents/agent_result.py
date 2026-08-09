"""
Agent Result Contract.

Defines the standard output returned by AI Agents.

All agents should return the same structure
so the Runtime can process results consistently.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentResult:
    """
    Immutable result returned after agent execution.

    Attributes:
        success:
            Indicates whether execution completed successfully.

        agent_id:
            Identifier of the agent that produced the result.

        output:
            Agent response payload.

        error:
            Error message when execution fails.
    """

    success: bool
    agent_id: str
    output: Any = None
    error: str | None = None