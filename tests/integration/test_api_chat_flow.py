"""
API chat flow integration tests.

Verifies the complete API boundary for the /chat endpoint
using a deterministic CompanionService test double.

Architecture:

HTTP
 |
 v
FastAPI /chat
 |
 v
CompanionService
 |
 v
ConversationAgent
 |
 v
LLMService
 |
 v
LLMProvider

External providers are intentionally not called.
"""

import pytest

from httpx import (
    ASGITransport,
    AsyncClient,
)

from backend.api import routes
from backend.api.main import app


class FakeCompanionService:
    """
    Deterministic CompanionService for API integration tests.
    """

    def __init__(
        self,
        character,
    ) -> None:
        self.character = character
        self.context = None
        self.use_research = None

    async def interact(
        self,
        context,
        use_research=False,
    ):
        """
        Capture the API-to-service contract and return
        a deterministic companion result.
        """

        self.context = context
        self.use_research = use_research

        return {
            "character": self.character.name,
            "conversation": {
                "character": self.character.name,
                "message": "Integration test response",
            },
            "research": (
                {
                    "query": context.request,
                }
                if use_research
                else None
            ),
            "quality": {
                "quality_score": 1.0,
                "passed": True,
                "findings": [],
                "recommendations": [],
            },
            "memory_count": 0,
        }


@pytest.mark.asyncio
async def test_chat_endpoint_executes_companion_service(
    monkeypatch,
):
    """
    Verify that /chat creates the correct execution
    context and delegates to CompanionService.
    """

    captured = {}

    def fake_factory(
        character,
    ):
        service = FakeCompanionService(
            character
        )

        captured["service"] = service

        return service

    monkeypatch.setattr(
        routes,
        "create_companion_service",
        fake_factory,
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/chat",
            json={
                "user_id": "integration-user",
                "character": "yeti",
                "message": (
                    "Explain artificial intelligence"
                ),
                "research": False,
            },
        )

    assert response.status_code == 200

    service = captured["service"]

    assert service.context is not None

    assert (
        service.context.user_id
        == "integration-user"
    )

    assert (
        service.context.request
        == "Explain artificial intelligence"
    )

    assert service.use_research is False

    data = response.json()

    assert data["character"] == "Yeti"

    assert (
        data["conversation"]["message"]
        == "Integration test response"
    )

    assert data["research"] is None


@pytest.mark.asyncio
async def test_chat_endpoint_enables_research(
    monkeypatch,
):
    """
    Verify that the API correctly forwards the
    research flag to CompanionService.
    """

    captured = {}

    def fake_factory(
        character,
    ):
        service = FakeCompanionService(
            character
        )

        captured["service"] = service

        return service

    monkeypatch.setattr(
        routes,
        "create_companion_service",
        fake_factory,
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/chat",
            json={
                "user_id": "integration-user",
                "character": "yeti",
                "message": (
                    "What is the EU AI Act?"
                ),
                "research": True,
            },
        )

    assert response.status_code == 200

    service = captured["service"]

    assert service.use_research is True

    assert service.context is not None

    assert (
        service.context.request
        == "What is the EU AI Act?"
    )

    data = response.json()

    assert data["research"] is not None

    assert (
        data["research"]["query"]
        == "What is the EU AI Act?"
    )