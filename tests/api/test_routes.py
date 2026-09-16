"""
API route tests.

These tests verify the HTTP/API boundary.

The tests deliberately replace the application service
with deterministic fakes so they never call:

- OpenAI
- Parallel
- external APIs
- real provider infrastructure

Architecture under test:

HTTP
|
v
API Route
|
v
CompanionService
|
v
Application Result
"""

import pytest

from httpx import (
    ASGITransport,
    AsyncClient,
)

from api.main import (
    app,
)

from api import (
    routes,
)


class FakeCompanionService:
    """
    Deterministic CompanionService test double.
    """

    def __init__(
        self,
        character,
    ) -> None:
        self.character = character
        self.received_context = None
        self.received_use_research = None

    async def interact(
        self,
        context,
        use_research=False,
    ):
        """
        Capture the application request and return
        a deterministic API result.
        """

        self.received_context = context

        self.received_use_research = (
            use_research
        )

        return {
            "character": self.character.name,

            "conversation": {
                "character": self.character.name,
                "message": (
                    f"{self.character.name}: "
                    "Test response"
                ),
                "intelligence_context": (
                    "TEST INTELLIGENCE"
                    if use_research
                    else None
                ),
            },

            "research": (
                {
                    "query": context.request,
                    "test": True,
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
async def test_chat_passes_research_false(
    monkeypatch,
):
    """
    /chat should pass research=False to the
    CompanionService.
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
                "user_id": "api-test-user",
                "character": "yeti",
                "message": (
                    "Explain artificial intelligence"
                ),
                "research": False,
            },
        )

    assert response.status_code == 200

    data = response.json()

    service = captured["service"]

    assert (
        service.received_use_research
        is False
    )

    assert (
        service.received_context.user_id
        == "api-test-user"
    )

    assert (
        service.received_context.request
        == "Explain artificial intelligence"
    )

    assert data["character"] == "Yeti"

    assert data["research"] is None

    assert (
        data["conversation"][
            "intelligence_context"
        ]
        is None
    )


@pytest.mark.asyncio
async def test_chat_passes_research_true(
    monkeypatch,
):
    """
    /chat should pass research=True to the
    CompanionService.
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
                "user_id": "api-test-user",
                "character": "yeti",
                "message": (
                    "What are the latest "
                    "European AI regulation "
                    "developments?"
                ),
                "research": True,
            },
        )

    assert response.status_code == 200

    data = response.json()

    service = captured["service"]

    assert (
        service.received_use_research
        is True
    )

    assert (
        service.received_context.user_id
        == "api-test-user"
    )

    assert (
        service.received_context.request
        == (
            "What are the latest "
            "European AI regulation "
            "developments?"
        )
    )

    assert data["character"] == "Yeti"

    assert data["research"] is not None

    assert (
        data["conversation"][
            "intelligence_context"
        ]
        == "TEST INTELLIGENCE"
    )


@pytest.mark.asyncio
async def test_chat_rejects_missing_message():
    """
    /chat should reject requests without a message.
    """

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
                "user_id": "api-test-user",
                "character": "yeti",
            },
        )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "message is required",
    }


@pytest.mark.asyncio
async def test_chat_rejects_unknown_character():
    """
    /chat should reject an unknown character.
    """

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
                "user_id": "api-test-user",
                "character": "does-not-exist",
                "message": "Hello",
            },
        )

    assert response.status_code == 400

    assert "does-not-exist" in (
        response.json()["detail"]
    )


@pytest.mark.asyncio
async def test_get_characters_returns_character_data():
    """
    /characters should expose the approved character
    registry through the API.
    """

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/characters"
        )

    assert response.status_code == 200

    data = response.json()

    assert "characters" in data

    assert isinstance(
        data["characters"],
        list,
    )

    assert len(
        data["characters"]
    ) > 0

    yeti = next(
        character
        for character in data["characters"]
        if character["id"] == "yeti"
    )

    assert yeti["name"] == "Yeti"

    assert "description" in yeti

    assert "personality" in yeti

    assert "learning_style" in yeti


@pytest.mark.asyncio
async def test_health_endpoint():
    """
    The root endpoint should expose the application
    health response.
    """

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/"
        )

    assert response.status_code == 200

    assert response.json() == {
        "status": "EasyChatBot running",
        "architecture": (
            "Runtime + Agents + Memory"
        ),
    }
