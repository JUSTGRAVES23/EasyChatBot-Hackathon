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
        self.created_world_ids.append(world_id)
        now = datetime.now(timezone.utc)

        return PrivateChatConversation(
            conversation_id=self.conversation_id,
            user_id=user_id,
            world_id=world_id,
            created_at=now,
            updated_at=now,
        )

    def send_message(
        self,
        *,
        user_id: str,
        world_id: str,
        conversation_id: UUID,
        message: str,
        character_instruction: str,
    ) -> PrivateChatResponse:
        self.sent_calls.append(
            {
                "user_id": user_id,
                "world_id": world_id,
                "conversation_id": conversation_id,
                "message": message,
                "character_instruction": character_instruction,
            }
        )

        now = datetime.now(timezone.utc)
        conversation = PrivateChatConversation(
            conversation_id=conversation_id,
            user_id=user_id,
            world_id=world_id,
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


def _principal(user_id: str = "user-123") -> Principal:
    return Principal(
        user_id=user_id,
        email="learner@example.com",
        email_verified=True,
        account_status="ACTIVE",
        roles=("BETA_USER",),
    )


@pytest.fixture
def private_chat_service() -> FakePrivateChatService:
    return FakePrivateChatService()


@pytest.fixture
def client(
    private_chat_service: FakePrivateChatService,
) -> TestClient:
    application = FastAPI()
    application.include_router(router)

    application.state.private_chat_service = private_chat_service
    application.state.private_chat_character_instruction = "French tutor"

    async def override_current_principal() -> Principal:
        return _principal()

    application.dependency_overrides[get_current_principal] = (
        override_current_principal
    )

    with TestClient(application) as test_client:
        yield test_client


def test_create_private_chat_requires_authentication() -> None:
    application = FastAPI()
    application.include_router(router)

    async def unauthenticated_principal() -> Principal:
        raise HTTPException(status_code=401, detail="Not authenticated")

    application.dependency_overrides[get_current_principal] = (
        unauthenticated_principal
    )

    with TestClient(application) as client:
        response = client.post(
            "/private-chat/conversations",
            json={"world_id": "french_world"},
        )

    assert response.status_code == 401


def test_create_private_chat_returns_conversation(
    client: TestClient,
    private_chat_service: FakePrivateChatService,
) -> None:
    response = client.post(
        "/private-chat/conversations",
        json={"world_id": "french_world"},
    )

    assert response.status_code == 201
    payload = response.json()

    assert payload["world_id"] == "french_world"
    assert UUID(payload["conversation_id"]) == (
        private_chat_service.conversation_id
    )
    assert private_chat_service.created_world_ids == ["french_world"]


@pytest.mark.parametrize(
    "payload",
    [
        {"world_id": ""},
        {"world_id": "   "},
    ],
)
def test_create_private_chat_rejects_invalid_world_id(
    client: TestClient,
    payload: dict[str, str],
) -> None:
    response = client.post(
        "/private-chat/conversations",
        json=payload,
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
            "world_id": "french_world",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["conversation_id"] == str(conversation_id)
    assert payload["world_id"] == "french_world"
    assert payload["response"] == "Bonjour !"
    assert payload["response_language"] == "fr"

    call = private_chat_service.sent_calls[0]
    assert call["user_id"] == "user-123"
    assert call["world_id"] == "french_world"
    assert call["character_instruction"] == "French tutor"


def test_send_private_chat_message_requires_authentication() -> None:
    application = FastAPI()
    application.include_router(router)

    async def unauthenticated_principal() -> Principal:
        raise HTTPException(status_code=401, detail="Not authenticated")

    application.dependency_overrides[get_current_principal] = (
        unauthenticated_principal
    )

    with TestClient(application) as client:
        response = client.post(
            "/private-chat/messages",
            json={
                "conversation_id": str(uuid4()),
                "world_id": "french_world",
                "message": "Bonjour",
            },
        )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
        "x" * 10_001,
    ],
)
def test_send_private_chat_message_rejects_invalid_message(
    client: TestClient,
    message: str,
) -> None:
    response = client.post(
        "/private-chat/messages",
        json={
            "conversation_id": str(uuid4()),
            "world_id": "french_world",
            "message": message,
        },
    )

    assert response.status_code == 422


def test_send_private_chat_message_rejects_client_language(
    client: TestClient,
) -> None:
    response = client.post(
        "/private-chat/messages",
        json={
            "conversation_id": str(uuid4()),
            "world_id": "french_world",
            "message": "Hello",
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
            "world_id": "french_world",
            "message": "Hello",
            "provider": "untrusted-provider",
            "model": "untrusted-model",
        },
    )

    assert response.status_code == 422
