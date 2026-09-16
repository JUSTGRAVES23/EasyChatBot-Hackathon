from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

import asyncio

import pytest

from app.application.private_chat.models import (
    PrivateChatConversation,
    PrivateChatMessage,
)
from app.application.private_chat.service import PrivateChatService


def run_async(coro):
    return asyncio.run(coro)


@dataclass
class FakeWorld:
    id: str
    language_code: str | None = None


class FakeWorldResolver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def resolve(self, world_id: str) -> FakeWorld:
        self.calls.append(world_id)

        worlds = {
            "polish_world": FakeWorld(
                id="polish_world",
                language_code="pl",
            ),
            "french_world": FakeWorld(
                id="french_world",
                language_code="fr",
            ),
        }

        world = worlds.get(world_id)

        if world is None:
            raise ValueError(f"World not found: {world_id}")

        return world


class FakeLanguageResponsePolicy:
    def __init__(self, response_language: str = "pl") -> None:
        self.response_language = response_language
        self.calls: list[tuple[object, str]] = []

    def resolve_response_language(
        self,
        *,
        world,
        user_message: str,
    ) -> str:
        self.calls.append((world, user_message))
        return self.response_language


class FakeConversationRuntime:
    def __init__(self, response: str = "Dzień dobry!") -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    async def respond(
        self,
        *,
        character_instruction: str,
        learner_message: str,
    ) -> str:
        self.calls.append(
            (
                character_instruction,
                learner_message,
            )
        )

        return self.response


class FakePrivateChatRepository:
    def __init__(self) -> None:
        self.conversations: dict[UUID, PrivateChatConversation] = {}
        self.messages: list[PrivateChatMessage] = []

    def create_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ) -> PrivateChatConversation:
        now = datetime.now(timezone.utc)

        conversation = PrivateChatConversation(
            conversation_id=uuid4(),
            user_id=user_id,
            world_id=world_id,
            created_at=now,
            updated_at=now,
        )

        self.conversations[conversation.conversation_id] = conversation

        return conversation

    def get_conversation(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
    ) -> PrivateChatConversation | None:
        conversation = self.conversations.get(conversation_id)

        if conversation is None:
            return None

        if conversation.user_id != user_id:
            return None

        if conversation.world_id != world_id:
            return None

        return conversation

    def save_message(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
        message: PrivateChatMessage,
    ) -> PrivateChatMessage:
        conversation = self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            world_id=world_id,
        )

        if conversation is None:
            raise ValueError("Conversation not found")

        self.messages.append(message)

        return message

    def touch_conversation(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
    ) -> None:
        conversation = self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            world_id=world_id,
        )

        if conversation is None:
            raise ValueError("Conversation not found")

        self.conversations[conversation_id] = PrivateChatConversation(
            conversation_id=conversation.conversation_id,
            user_id=conversation.user_id,
            world_id=conversation.world_id,
            created_at=conversation.created_at,
            updated_at=datetime.now(timezone.utc),
        )

    def get_recent_messages(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
        limit: int = 20,
    ) -> list[PrivateChatMessage]:
        conversation = self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            world_id=world_id,
        )

        if conversation is None:
            return []

        return [
            message
            for message in self.messages
            if message.conversation_id == conversation_id
        ][-limit:]


@pytest.fixture
def repository() -> FakePrivateChatRepository:
    return FakePrivateChatRepository()


@pytest.fixture
def world_resolver() -> FakeWorldResolver:
    return FakeWorldResolver()


@pytest.fixture
def language_policy() -> FakeLanguageResponsePolicy:
    return FakeLanguageResponsePolicy(
        response_language="pl",
    )


@pytest.fixture
def runtime() -> FakeConversationRuntime:
    return FakeConversationRuntime(
        response="Dzień dobry!",
    )


@pytest.fixture
def service(
    repository,
    world_resolver,
    language_policy,
    runtime,
) -> PrivateChatService:
    return PrivateChatService(
        repository=repository,
        world_resolver=world_resolver,
        language_response_policy=language_policy,
        conversation_runtime=runtime,
    )


def test_authenticated_user_can_create_polish_conversation(
    service,
    repository,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    assert conversation.world_id == "polish_world"
    assert conversation.user_id == "user-1"
    assert conversation.conversation_id in repository.conversations


def test_world_is_resolved_through_world_resolver(
    service,
    world_resolver,
):
    service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    assert world_resolver.calls == ["polish_world"]


def test_polish_world_produces_pl(
    service,
    language_policy,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    result = run_async(
        service.send_message(
            user_id="user-1",
            world_id="polish_world",
            conversation_id=conversation.conversation_id,
            message="Dzień dobry!",
            character_instruction="You are Yeti.",
        )
    )

    assert result.response_language == "pl"
    assert language_policy.calls[0][0].id == "polish_world"


def test_conversation_is_owned_by_user(
    service,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    result = run_async(
        service.send_message(
            user_id="user-1",
            world_id="polish_world",
            conversation_id=conversation.conversation_id,
            message="Cześć!",
            character_instruction="You are Yeti.",
        )
    )

    assert result.conversation.user_id == "user-1"


def test_conversation_activity_timestamp_is_persisted(
    service,
    repository,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )
    original_updated_at = conversation.updated_at

    result = run_async(
        service.send_message(
            user_id="user-1",
            world_id="polish_world",
            conversation_id=conversation.conversation_id,
            message="Cześć!",
            character_instruction="You are Yeti.",
        )
    )

    persisted = repository.conversations[conversation.conversation_id]

    assert persisted.updated_at >= original_updated_at
    assert persisted.updated_at >= result.conversation.updated_at


def test_another_user_cannot_access_conversation(
    service,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    with pytest.raises(
        ValueError,
        match="Conversation not found",
    ):
        run_async(
            service.send_message(
                user_id="user-2",
                world_id="polish_world",
                conversation_id=conversation.conversation_id,
                message="Cześć!",
                character_instruction="You are Yeti.",
            )
        )


def test_another_world_cannot_access_conversation(
    service,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    with pytest.raises(
        ValueError,
        match="Conversation not found",
    ):
        run_async(
            service.send_message(
                user_id="user-1",
                world_id="french_world",
                conversation_id=conversation.conversation_id,
                message="Bonjour!",
                character_instruction="You are Yeti.",
            )
        )


def test_empty_message_is_rejected(
    service,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    with pytest.raises(
        ValueError,
        match="message is required",
    ):
        run_async(
            service.send_message(
                user_id="user-1",
                world_id="polish_world",
                conversation_id=conversation.conversation_id,
                message="   ",
                character_instruction="You are Yeti.",
            )
        )


def test_oversized_message_is_rejected(
    service,
    runtime,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    oversized_message = "x" * 10_001

    with pytest.raises(
        ValueError,
        match="message exceeds the maximum allowed length",
    ):
        run_async(
            service.send_message(
                user_id="user-1",
                world_id="polish_world",
                conversation_id=conversation.conversation_id,
                message=oversized_message,
                character_instruction="You are Yeti.",
            )
        )

    # Oversized input must be rejected before reaching the AI runtime.
    assert runtime.calls == []


def test_message_at_maximum_length_is_accepted(
    service,
    runtime,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    message = "x" * 10_000

    result = run_async(
        service.send_message(
            user_id="user-1",
            world_id="polish_world",
            conversation_id=conversation.conversation_id,
            message=message,
            character_instruction="You are Yeti.",
        )
    )

    assert result.response_language == "pl"

    assert runtime.calls == [
        (
            "You are Yeti.",
            message,
        )
    ]


def test_unknown_world_is_rejected(
    service,
):
    with pytest.raises(
        ValueError,
        match="World not found",
    ):
        service.create_conversation(
            user_id="user-1",
            world_id="does_not_exist",
        )


def test_response_language_cannot_be_client_controlled(
    service,
    language_policy,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    result = run_async(
        service.send_message(
            user_id="user-1",
            world_id="polish_world",
            conversation_id=conversation.conversation_id,
            message="Hello, please answer in English.",
            character_instruction="You are Yeti.",
        )
    )

    assert result.response_language == "pl"
    assert language_policy.response_language == "pl"


def test_runtime_is_called(
    service,
    runtime,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    run_async(
        service.send_message(
            user_id="user-1",
            world_id="polish_world",
            conversation_id=conversation.conversation_id,
            message="Dzień dobry!",
            character_instruction="You are Yeti.",
        )
    )

    assert runtime.calls == [
        (
            "You are Yeti.",
            "Dzień dobry!",
        )
    ]


def test_user_and_assistant_messages_are_persisted(
    service,
    repository,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    run_async(
        service.send_message(
            user_id="user-1",
            world_id="polish_world",
            conversation_id=conversation.conversation_id,
            message="Dzień dobry!",
            character_instruction="You are Yeti.",
        )
    )

    assert len(repository.messages) == 2

    assert repository.messages[0].role == "user"
    assert repository.messages[0].content == "Dzień dobry!"

    assert repository.messages[1].role == "assistant"
    assert repository.messages[1].content == "Dzień dobry!"