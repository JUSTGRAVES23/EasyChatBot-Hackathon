from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.dependencies.identity import get_current_principal
from app.api.private_chat import router
from app.application.private_chat.models import (
    PrivateChatConversation,
    PrivateChatMessage,
    PrivateChatResponse,
)
from app.domain.identity.principal import Principal


class FakePrivateChatService:
    """Async application-service double for private-chat API tests."""

    VALID_WORLD_IDS = {
        "french_world",
        "polish_world",
    }

    def __init__(self) -> None:
        self.created_world_ids: list[str] = []
        self.sent_calls: list[dict[str, object]] = []
        self.conversation_id = uuid4()

    def create_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ) -> PrivateChatConversation:
        if world_id not in self.VALID_WORLD_IDS:
            raise ValueError("World not found")

        self.created_world_ids.append(world_id)

        now = datetime.now(timezone.utc)

        return PrivateChatConversation(
            conversation_id=self.conversation_id,
            user_id=user_id,
            world_id=world_id,
            created_at=now,
            updated_at=now,
        )

    async def send_message(
        self,
        *,
        user_id: str,
        conversation_id: UUID,
        message: str,
    ) -> PrivateChatResponse:
        """
        Async application-service double matching the production API contract.

        The World is derived from the authenticated conversation rather than
        trusting a client-supplied World or language on every message.
        """
        self.sent_calls.append(
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "message": message,
            }
        )

        now = datetime.now(timezone.utc)

        conversation = PrivateChatConversation(
            conversation_id=conversation_id,
            user_id=user_id,
            world_id="french_world",
            created_at=now,
            updated_at=now,
        )

        return PrivateChatResponse(
            conversation=conversation,
            user_message=PrivateChatMessage(
                conversation_id=conversation_id,
                role="user",
                content=message,
                created_at=now,
            ),
            assistant_message=PrivateChatMessage(
                conversation_id=conversation_id,
                role="assistant",
                content="Bonjour !",
                created_at=now,
            ),
            response_language="fr",
        )

    def close(self) -> None:
        """Close the fake service using the same lifecycle contract as production."""
        return None


def _principal(
    *,
    user_id: str = "user-123",
    email: str = "learner@example.com",
    roles: tuple[str, ...] = ("BETA_USER",),
) -> Principal:
    return Principal(
        user_id=user_id,
        email=email,
        email_verified=True,
        account_status="ACTIVE",
        roles=roles,
    )


@pytest.fixture
def private_chat_service() -> FakePrivateChatService:
    return FakePrivateChatService()


@pytest.fixture
def app(
    private_chat_service: FakePrivateChatService,
) -> FastAPI:
    application = FastAPI()
    application.include_router(router)

    application.state.private_chat_service_factory = (
        lambda: private_chat_service
    )

    return application


@pytest.fixture
def client(
    app: FastAPI,
) -> TestClient:
    async def fake_get_current_principal() -> Principal:
        return _principal()

    app.dependency_overrides[
        get_current_principal
    ] = fake_get_current_principal

    return TestClient(app)


def test_create_private_chat_returns_conversation(
    client: TestClient,
    private_chat_service: FakePrivateChatService,
) -> None:
    response = client.post(
        "/private-chat/conversations",
        json={
            "world_id": "polish_world",
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["conversation_id"] == str(
        private_chat_service.conversation_id
    )
    assert payload["world_id"] == "polish_world"

    assert private_chat_service.created_world_ids == ["polish_world"]


def test_create_private_chat_requires_authentication(
    app: FastAPI,
) -> None:
    async def reject_current_principal() -> Principal:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    app.dependency_overrides[
        get_current_principal
    ] = reject_current_principal

    client = TestClient(app)

    response = client.post(
        "/private-chat/conversations",
        json={
            "world_id": "polish_world",
        },
    )

    assert response.status_code == 401


def test_create_private_chat_rejects_invalid_world(
    client: TestClient,
) -> None:
    response = client.post(
        "/private-chat/conversations",
        json={
            "world_id": "not_a_real_world",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "World not found"


def test_create_private_chat_does_not_accept_client_user_id(
    client: TestClient,
) -> None:
    response = client.post(
        "/private-chat/conversations",
        json={
            "world_id": "polish_world",
            "user_id": "attacker-user",
        },
    )

    assert response.status_code == 422


def test_send_private_chat_message_returns_response(
    client: TestClient,
    private_chat_service: FakePrivateChatService,
) -> None:
    conversation_id = private_chat_service.conversation_id

    response = client.post(
        "/private-chat/messages",
        json={
            "conversation_id": str(conversation_id),
            "message": "Bonjour",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    # The production HTTP response is intentionally flattened.
    assert payload["conversation_id"] == str(conversation_id)
    assert payload["world_id"] == "french_world"
    assert payload["response"] == "Bonjour !"
    assert payload["response_language"] == "fr"

    assert len(private_chat_service.sent_calls) == 1

    sent_call = private_chat_service.sent_calls[0]

    assert sent_call["user_id"] == "user-123"
    assert sent_call["conversation_id"] == conversation_id
    assert sent_call["message"] == "Bonjour"


def test_send_private_chat_message_requires_authentication(
    app: FastAPI,
    private_chat_service: FakePrivateChatService,
) -> None:
    async def reject_current_principal() -> Principal:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    app.dependency_overrides[
        get_current_principal
    ] = reject_current_principal

    client = TestClient(app)

    response = client.post(
        "/private-chat/messages",
        json={
            "conversation_id": str(private_chat_service.conversation_id),
            "message": "Bonjour",
        },
    )

    assert response.status_code == 401


def test_send_private_chat_message_rejects_invalid_message(
    client: TestClient,
    private_chat_service: FakePrivateChatService,
) -> None:
    response = client.post(
        "/private-chat/messages",
        json={
            "conversation_id": str(private_chat_service.conversation_id),
            "message": "",
        },
    )

    assert response.status_code == 422


def test_send_private_chat_message_rejects_invalid_conversation_id(
    client: TestClient,
) -> None:
    response = client.post(
        "/private-chat/messages",
        json={
            "conversation_id": "not-a-uuid",
            "message": "Bonjour",
        },
    )

    assert response.status_code == 422


def test_send_private_chat_message_does_not_accept_client_world_override(
    client: TestClient,
    private_chat_service: FakePrivateChatService,
) -> None:
    response = client.post(
        "/private-chat/messages",
        json={
            "conversation_id": str(private_chat_service.conversation_id),
            "message": "Bonjour",
            "world_id": "polish_world",
        },
    )

    assert response.status_code == 422


def test_send_private_chat_message_does_not_accept_client_language_override(
    client: TestClient,
    private_chat_service: FakePrivateChatService,
) -> None:
    response = client.post(
        "/private-chat/messages",
        json={
            "conversation_id": str(private_chat_service.conversation_id),
            "message": "Bonjour",
            "language": "en",
        },
    )

    assert response.status_code == 422


def test_send_private_chat_message_rejects_client_provider_and_model(
    client: TestClient,
) -> None:
    response = client.post(
        "/private-chat/messages",
        json={
            "conversation_id": str(uuid4()),
            "message": "Hello",
            "provider": "untrusted-provider",
            "model": "untrusted-model",
        },
    )

    assert response.status_code == 422