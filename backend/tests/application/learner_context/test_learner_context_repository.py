from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.application.learner_context.postgresql_repository import (
    CrossChannelLearnerContextRepository,
)


@dataclass(frozen=True)
class Binding:
    telegram_user_id: str


@dataclass(frozen=True)
class Memory:
    memory_key: str
    memory_value: str


@dataclass(frozen=True)
class Event:
    role: str
    content: str


@dataclass(frozen=True)
class World:
    world_id: str
    language_code: str


class FakeBindings:
    def __init__(self, binding=None):
        self.binding = binding
        self.calls = []

    async def get_by_user_id(self, user_id: str):
        self.calls.append(user_id)
        return self.binding


class FakeMemoryRepository:
    def __init__(self, memories=None):
        self.memories = memories or []
        self.calls = []

    async def get_user_memories(self, *, telegram_user_id, world_id):
        self.calls.append((telegram_user_id, world_id))
        return list(self.memories)


class FakeEventRepository:
    def __init__(self, events=None):
        self.events = events or []
        self.calls = []

    async def get_recent(
        self,
        *,
        telegram_user_hash,
        conversation_id,
        world_id,
        limit=20,
    ):
        self.calls.append(
            {
                "telegram_user_hash": telegram_user_hash,
                "conversation_id": conversation_id,
                "world_id": world_id,
                "limit": limit,
            }
        )
        return list(self.events)[:limit]


class FakePrivacy:
    def __init__(self):
        self.calls = []

    def pseudonymize_identifier(self, value: str) -> str:
        self.calls.append(value)
        return f"hash-{value}"


class FakeWorldResolver:
    def __init__(self, world):
        self.world = world
        self.calls = []

    def resolve(self, world_id: str):
        self.calls.append(world_id)
        if world_id != self.world.world_id:
            raise ValueError(f"World not found: {world_id}")
        return self.world


def make_repository(*, binding=None, memories=None, events=None):
    bindings = FakeBindings(binding)
    memory = FakeMemoryRepository(memories)
    events_repo = FakeEventRepository(events)
    privacy = FakePrivacy()
    resolver = FakeWorldResolver(
        World(world_id="world-fr", language_code="fr")
    )

    repository = CrossChannelLearnerContextRepository(
        telegram_bindings=bindings,
        memory_repository=memory,
        conversation_event_repository=events_repo,
        privacy_identifier_service=privacy,
        world_resolver=resolver,
    )

    return repository, bindings, memory, events_repo, privacy, resolver


@pytest.mark.asyncio
async def test_unconnected_learner_returns_world_context_without_telegram_data():
    repository, bindings, memory, events, privacy, resolver = make_repository()

    context = await repository.get(
        learner_id="learner-1",
        world_id="world-fr",
        recent_limit=20,
    )

    assert context is not None
    assert context.learner_id == "learner-1"
    assert context.world_id == "world-fr"
    assert context.language_code == "fr"
    assert context.character == "Alix"
    assert context.level == "B1"
    assert context.telegram_connected is False
    assert context.learning_memories == ()
    assert context.recent_learning_context == ()
    assert bindings.calls == ["learner-1"]
    assert memory.calls == []
    assert events.calls == []
    assert privacy.calls == []
    assert resolver.calls == ["world-fr"]


@pytest.mark.asyncio
async def test_connected_learner_reuses_existing_telegram_identity_and_world_scope():
    repository, bindings, memory, events, privacy, resolver = make_repository(
        binding=Binding(telegram_user_id="12345"),
        memories=[
            Memory("grammar_mistake", "Uses articles incorrectly."),
            Memory("vocabulary", "Needs more travel vocabulary."),
        ],
        events=[
            Event("user", "Bonjour"),
            Event("assistant", "Continuons en français."),
        ],
    )

    context = await repository.get(
        learner_id="learner-1",
        world_id="world-fr",
        recent_limit=10,
    )

    assert context.telegram_connected is True
    assert context.learning_memories[0].memory_type == "grammar_mistake"
    assert context.learning_memories[0].content == "Uses articles incorrectly."
    assert context.learning_memories[1].memory_type == "vocabulary"
    assert context.recent_learning_context[0].role == "user"
    assert context.recent_learning_context[0].content == "Bonjour"
    assert context.recent_learning_context[1].role == "assistant"
    assert context.recent_learning_context[1].content == "Continuons en français."

    assert memory.calls == [("12345", "world-fr")]
    assert privacy.calls == ["12345"]
    assert events.calls == [
        {
            "telegram_user_hash": "hash-12345",
            "conversation_id": "telegram-hash-12345",
            "world_id": "world-fr",
            "limit": 10,
        }
    ]


@pytest.mark.asyncio
async def test_recent_context_is_bounded_by_requested_limit():
    repository, *_rest = make_repository(
        binding=Binding(telegram_user_id="12345"),
        events=[
            Event("user", "one"),
            Event("assistant", "two"),
            Event("user", "three"),
        ],
    )

    context = await repository.get(
        learner_id="learner-1",
        world_id="world-fr",
        recent_limit=2,
    )

    assert [item.content for item in context.recent_learning_context] == [
        "one",
        "two",
    ]


@pytest.mark.asyncio
async def test_unknown_world_fails_closed_before_telegram_projection():
    repository, bindings, memory, events, privacy, resolver = make_repository(
        binding=Binding(telegram_user_id="12345")
    )

    with pytest.raises(ValueError, match="World not found"):
        await repository.get(
            learner_id="learner-1",
            world_id="unknown-world",
            recent_limit=20,
        )

    assert bindings.calls == []
    assert memory.calls == []
    assert events.calls == []
    assert privacy.calls == []
    assert resolver.calls == ["unknown-world"]


@pytest.mark.asyncio
async def test_raw_telegram_identity_is_not_exposed_in_application_projection():
    repository, *_rest = make_repository(
        binding=Binding(telegram_user_id="12345"),
        memories=[Memory("vocabulary", "hotel")],
        events=[Event("user", "Bonjour")],
    )

    context = await repository.get(
        learner_id="learner-1",
        world_id="world-fr",
        recent_limit=20,
    )

    assert not hasattr(context, "telegram_user_id")
    assert not hasattr(context, "telegram_user_hash")
    assert "12345" not in repr(context)
    assert "hash-12345" not in repr(context)
