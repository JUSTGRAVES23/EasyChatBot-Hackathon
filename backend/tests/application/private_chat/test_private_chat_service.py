from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.application.private_chat.models import (
    PrivateChatActiveConversation,
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
            "polish_world": FakeWorld("polish_world", "pl"),
            "french_world": FakeWorld("french_world", "fr"),
        }
        world = worlds.get(world_id)
        if world is None:
            raise ValueError(f"World not found: {world_id}")
        return world


class FakeLanguageDetector:
    def detect(self, text: str) -> str:
        return "pl"


class FakeLanguageResponsePolicy:
    def __init__(self, response_language: str = "pl") -> None:
        self.response_language = response_language
        self.calls: list[tuple[object, str, object]] = []

    def resolve_response_language(
        self,
        *,
        world,
        user_message: str,
        language_detector,
    ) -> str:
        self.calls.append(
            (world, user_message, language_detector)
        )
        return self.response_language


class FakeConversationRuntime:
    def __init__(self, response: str = "DzieÅ„ dobry!") -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    async def respond(
        self,
        *,
        character_instruction: str,
        learner_message: str,
    ) -> str:
        self.calls.append((character_instruction, learner_message))
        return self.response


class FakePrivateChatRepository:
    def __init__(self) -> None:
        self.conversations: dict[UUID, PrivateChatConversation] = {}
        self.messages: list[PrivateChatMessage] = {}

        # Server-owned active conversation pointer:
        #
        # (user_id, world_id) -> conversation_id
        #
        # This mirrors the production active-conversation concept without
        # requiring a database for application-service unit tests.
        self.active_conversations: dict[tuple[str, str], UUID] = {}

        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

        # Keep messages as a list for compatibility with the existing tests.
        self.messages = []

    def get_conversation_for_user(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
    ) -> PrivateChatConversation | None:
        conversation = self.conversations.get(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            return None
        return conversation

    def get_active_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
        limit: int = 20,
    ) -> PrivateChatActiveConversation | None:
        if limit < 1:
            raise ValueError("limit must be greater than zero")

        conversation_id = self.active_conversations.get(
            (user_id, world_id)
        )

        if conversation_id is None:
            return None

        conversation = self.get_conversation_for_user(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None or conversation.world_id != world_id:
            return None

        messages = self.get_recent_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            world_id=world_id,
            limit=limit,
        )

        return PrivateChatActiveConversation(
            conversation=conversation,
            messages=messages,
        )

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

    def set_active_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
        conversation_id: UUID,
    ) -> None:
        conversation = self.get_conversation_for_user(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None or conversation.world_id != world_id:
            raise ValueError(
                "Private chat conversation not found"
            )

        self.active_conversations[(user_id, world_id)] = (
            conversation_id
        )

    def save_message(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
        message: PrivateChatMessage,
    ) -> PrivateChatMessage:
        conversation = self.get_conversation_for_user(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None or conversation.world_id != world_id:
            raise ValueError("Conversation not found")

        self.messages.append(message)

        return message

    def get_recent_messages(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
        limit: int = 20,
    ) -> list[PrivateChatMessage]:
        if limit < 1:
            raise ValueError("limit must be greater than zero")

        conversation = self.get_conversation_for_user(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None or conversation.world_id != world_id:
            return []

        messages = [
            message
            for message in self.messages
            if message.conversation_id == conversation_id
        ]

        return messages[-limit:]

    def touch_conversation(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
    ) -> None:
        conversation = self.get_conversation_for_user(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None or conversation.world_id != world_id:
            raise ValueError("Conversation not found")

        self.conversations[conversation_id] = (
            PrivateChatConversation(
                conversation_id=conversation.conversation_id,
                user_id=conversation.user_id,
                world_id=conversation.world_id,
                created_at=conversation.created_at,
                updated_at=datetime.now(timezone.utc),
            )
        )

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.close_count += 1


@pytest.fixture
def repository():
    return FakePrivateChatRepository()


@pytest.fixture
def world_resolver():
    return FakeWorldResolver()


@pytest.fixture
def language_policy():
    return FakeLanguageResponsePolicy()


@pytest.fixture
def runtime():
    return FakeConversationRuntime()


@pytest.fixture
def service(repository, world_resolver, language_policy, runtime):
    return PrivateChatService(
        repository=repository,
        world_resolver=world_resolver,
        language_response_policy=language_policy,
        language_detector=FakeLanguageDetector(),
        conversation_runtime=runtime,
        character_instruction="You are Yeti.",
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

    # Creating a conversation explicitly is also the Restart operation,
    # therefore the new conversation must become active.
    assert repository.active_conversations[
        ("user-1", "polish_world")
    ] == conversation.conversation_id

    assert repository.commit_count == 1


def test_first_active_lookup_creates_and_activates_conversation(
    service,
    repository,
):
    active = service.get_active_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    assert active.conversation.user_id == "user-1"
    assert active.conversation.world_id == "polish_world"
    assert active.messages == []

    assert (
        repository.active_conversations[
            ("user-1", "polish_world")
        ]
        == active.conversation.conversation_id
    )

    assert len(repository.conversations) == 1
    assert repository.commit_count == 1


def test_repeated_active_lookup_returns_same_conversation(
    service,
    repository,
):
    first = service.get_active_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    first_id = first.conversation.conversation_id

    second = service.get_active_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    second_id = second.conversation.conversation_id

    assert second_id == first_id

    # The second lookup must resume the existing conversation rather
    # than creating another conversation.
    assert len(repository.conversations) == 1

    # No additional commit is required when simply resuming an existing
    # active conversation.
    assert repository.commit_count == 1


def test_active_lookup_returns_existing_history(
    service,
    repository,
):
    conversation = service.get_active_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    run_async(
        service.send_message(
            user_id="user-1",
            conversation_id=conversation.conversation.conversation_id,
            message="CzeÅ›Ä‡!",
        )
    )

    resumed = service.get_active_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    assert resumed.conversation.conversation_id == (
        conversation.conversation.conversation_id
    )

    assert [message.role for message in resumed.messages] == [
        "user",
        "assistant",
    ]

    assert resumed.messages[0].content == "CzeÅ›Ä‡!"


def test_restart_creates_new_active_conversation_and_preserves_old_one(
    service,
    repository,
):
    first = service.get_active_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    first_id = first.conversation.conversation_id

    run_async(
        service.send_message(
            user_id="user-1",
            conversation_id=first_id,
            message="CzeÅ›Ä‡!",
        )
    )

    restarted = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    second_id = restarted.conversation_id

    assert second_id != first_id

    # The new conversation is active.
    assert repository.active_conversations[
        ("user-1", "polish_world")
    ] == second_id

    # The old conversation remains persisted.
    assert first_id in repository.conversations

    # Its messages remain persisted.
    old_messages = [
        message
        for message in repository.messages
        if message.conversation_id == first_id
    ]

    assert len(old_messages) == 2

    # The new conversation starts empty.
    new_messages = [
        message
        for message in repository.messages
        if message.conversation_id == second_id
    ]

    assert new_messages == []

    assert len(repository.conversations) == 2


def test_send_message_does_not_change_active_conversation(
    service,
    repository,
):
    active = service.get_active_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    conversation_id = active.conversation.conversation_id

    assert repository.active_conversations[
        ("user-1", "polish_world")
    ] == conversation_id

    run_async(
        service.send_message(
            user_id="user-1",
            conversation_id=conversation_id,
            message="DzieÅ„ dobry!",
        )
    )

    # Sending messages must not silently switch the active pointer.
    assert repository.active_conversations[
        ("user-1", "polish_world")
    ] == conversation_id


def test_polish_world_produces_pl(
    service,
    language_policy,
    repository,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    result = run_async(
        service.send_message(
            user_id="user-1",
            conversation_id=conversation.conversation_id,
            message="DzieÅ„ dobry!",
        )
    )

    assert result.response_language == "pl"
    assert language_policy.calls[0][0].id == "polish_world"
    assert repository.messages[0].role == "user"
    assert repository.messages[1].role == "assistant"


def test_world_is_derived_from_persisted_conversation(
    service,
    world_resolver,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    # Ignore the resolver call made while creating the conversation.
    # The assertion below verifies that send_message independently
    # derives the World from the persisted conversation.
    world_resolver.calls.clear()

    run_async(
        service.send_message(
            user_id="user-1",
            conversation_id=conversation.conversation_id,
            message="CzeÅ›Ä‡!",
        )
    )

    assert world_resolver.calls == ["polish_world"]


def test_another_user_cannot_access_conversation(service):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    with pytest.raises(ValueError, match="Conversation not found"):
        run_async(
            service.send_message(
                user_id="user-2",
                conversation_id=conversation.conversation_id,
                message="CzeÅ›Ä‡!",
            )
        )


def test_client_cannot_change_world_of_existing_conversation(service):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    # send_message has no world_id argument by design.
    with pytest.raises(TypeError):
        run_async(
            service.send_message(
                user_id="user-1",
                conversation_id=conversation.conversation_id,
                message="Bonjour!",
                world_id="french_world",
            )
        )


def test_response_language_is_application_controlled(
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
            conversation_id=conversation.conversation_id,
            message="Please answer in English.",
        )
    )

    assert result.response_language == "pl"
    assert language_policy.response_language == "pl"


def test_message_length_is_enforced_before_runtime(
    service,
    runtime,
):
    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    with pytest.raises(
        ValueError,
        match="message exceeds the maximum allowed length",
    ):
        run_async(
            service.send_message(
                user_id="user-1",
                conversation_id=conversation.conversation_id,
                message="x" * 10_001,
            )
        )

    assert runtime.calls == []


def test_runtime_uses_server_controlled_character_instruction(
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
            conversation_id=conversation.conversation_id,
            message="DzieÅ„ dobry!",
        )
    )

    assert runtime.calls == [
        ("You are Yeti.", "DzieÅ„ dobry!")
    ]


def test_runtime_failure_does_not_persist_messages(
    service,
    repository,
):
    class FailingRuntime:
        async def respond(
            self,
            *,
            character_instruction,
            learner_message,
        ):
            raise RuntimeError("provider failure")

    service = PrivateChatService(
        repository=repository,
        world_resolver=FakeWorldResolver(),
        language_response_policy=FakeLanguageResponsePolicy(),
        language_detector=FakeLanguageDetector(),
        conversation_runtime=FailingRuntime(),
        character_instruction="You are Yeti.",
    )

    conversation = service.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    with pytest.raises(
        RuntimeError,
        match="provider failure",
    ):
        run_async(
            service.send_message(
                user_id="user-1",
                conversation_id=conversation.conversation_id,
                message="CzeÅ›Ä‡!",
            )
        )

    assert repository.messages == []


def test_service_closes_request_scoped_repository(
    service,
    repository,
):
    service.close()

    assert repository.close_count == 1