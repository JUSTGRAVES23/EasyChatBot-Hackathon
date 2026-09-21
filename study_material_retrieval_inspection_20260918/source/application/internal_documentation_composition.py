from pathlib import Path

from src.ai_agents.internal_documentation_agent.composition import (
    create_internal_documentation_agent,
)
from src.ai_agents.internal_documentation_agent.filesystem_knowledge_provider import (
    FilesystemKnowledgeProvider,
)


def create_internal_documentation_provider() -> FilesystemKnowledgeProvider:
    """Create the explicitly configured internal documentation provider."""

    root = Path(__file__).resolve().parents[2] / "docs"

    return FilesystemKnowledgeProvider(
        roots=[root],
    )


def create_internal_documentation_agent_from_repository():
    """Compose the read-only internal documentation agent."""

    provider = create_internal_documentation_provider()

    return create_internal_documentation_agent(
        knowledge_provider=provider,
    )
