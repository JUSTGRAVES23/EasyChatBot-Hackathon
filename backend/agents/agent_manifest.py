"""
Agent Manifest Definition.

The AgentManifest describes the identity and basic metadata
of an EasyChatBot AI Agent.

The manifest does not execute the agent.
It only defines:
- who the agent is
- what the agent represents
- its version information

Execution is handled by the AI Runtime.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentManifest:
    """
    Immutable definition of an AI Agent.

    Agents are identified through their manifest.
    The Runtime uses this information for controlled execution.

    Attributes:
        agent_id:
            Unique identifier of the agent.

        name:
            Human-readable agent name.

        description:
            Purpose and responsibility of the agent.

        version:
            Version of the agent definition.
    """

    agent_id: str
    name: str
    description: str
    version: str = "1.0.0"