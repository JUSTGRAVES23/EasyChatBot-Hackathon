from __future__ import annotations

from .agent import InternalDocumentationAgent
from .knowledge_provider import KnowledgeProvider


def create_internal_documentation_agent(
    knowledge_provider: KnowledgeProvider,
) -> InternalDocumentationAgent:
    """Composition root for the capability.

    Wire the existing governed Project Brain/knowledge implementation here.
    Do not instantiate an external provider or SDK.
    """
    return InternalDocumentationAgent(knowledge_provider)
