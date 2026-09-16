import pytest

from httpx import ASGITransport, AsyncClient

from api.main import app
from api import routes


class FakeCompanionService:
    """
    Test double for the application service.

    This test deliberately does not invoke Parallel.
    """

    def __init__(
        self,
        character,
    ):
        self.character = character
        self.received_context = None
        self.received_use_research = None

    async def interact(
        self,
        context,
        use_research=False,
    ):
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
                    f"Test response"
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
    Verify /chat passes research=False
    to CompanionService.
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
    Verify /chat passes research=True
    to CompanionService.

    This is an API contract test and therefore
    intentionally does not call Parallel.
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
