"""Unit tests for WorldTelegramDestinationService."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.world_catalogue.models import LearningWorldCatalogueEntry
from app.application.world_telegram.service import (
    WorldTelegramDestinationService,
)
from app.domain.world_telegram import (
    TelegramDestinationType,
    WorldTelegramDestination,
)


class FakeDestinationRepository:
    def __init__(self):
        self.items = {}

    def get_by_id(self, destination_id):
        return self.items.get(destination_id)

    def get_by_world_and_chat(self, *, world_id, telegram_chat_id):
        return next(
            (
                item
                for item in self.items.values()
                if item.world_id == world_id
                and item.telegram_chat_id == telegram_chat_id
            ),
            None,
        )

    def list_by_world(self, world_id):
        return tuple(
            item
            for item in self.items.values()
            if item.world_id == world_id
        )

    def save(self, destination):
        self.items[destination.id] = destination
        return destination

    def delete(self, destination_id):
        return self.items.pop(destination_id, None) is not None


class FakeWorldCatalogueRepository:
    def __init__(self, worlds):
        self.worlds = worlds

    def get_by_identifier(self, identifier):
        return next(
            (
                world
                for world in self.worlds.values()
                if world.identifier == identifier
            ),
            None,
        )

    def get_by_id(self, world_id):
        return self.worlds.get(world_id)

    def list_all(self):
        return tuple(self.worlds.values())


def make_world(
    *,
    world_id=None,
    identifier="french_world",
    enabled=True,
):
    return LearningWorldCatalogueEntry(
        id=world_id or uuid4(),
        identifier=identifier,
        name="French World",
        description="French learning World for testing.",
        language="French",
        version="1.0",
        status="ACTIVE",
        enabled=enabled,
        world_type="LANGUAGE",
        learning_domain="LANGUAGE_LEARNING",
        runtime_world_id="french-runtime",
    )


def make_service(world):
    return WorldTelegramDestinationService(
        repository=FakeDestinationRepository(),
        world_catalogue_repository=FakeWorldCatalogueRepository(
            {world.id: world}
        ),
    )


def test_service_registers_destination_for_authoritative_world():
    world = make_world()
    repository = FakeDestinationRepository()

    service = WorldTelegramDestinationService(
        repository=repository,
        world_catalogue_repository=FakeWorldCatalogueRepository(
            {world.id: world}
        ),
    )

    destination = service.register_destination(
        world_id=world.id,
        telegram_chat_id=" -100123 ",
        destination_type=TelegramDestinationType.GROUP,
    )

    assert destination.world_id == world.id
    assert destination.telegram_chat_id == "-100123"
    assert destination.destination_type == TelegramDestinationType.GROUP
    assert destination.enabled is True
    assert repository.get_by_id(destination.id) == destination


def test_service_rejects_unknown_world():
    repository = FakeDestinationRepository()
    service = WorldTelegramDestinationService(
        repository=repository,
        world_catalogue_repository=FakeWorldCatalogueRepository({}),
    )

    unknown_world_id = uuid4()

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        service.register_destination(
            world_id=unknown_world_id,
            telegram_chat_id="-100123",
            destination_type=TelegramDestinationType.GROUP,
        )


def test_service_rejects_duplicate_destination():
    world = make_world()
    repository = FakeDestinationRepository()

    service = WorldTelegramDestinationService(
        repository=repository,
        world_catalogue_repository=FakeWorldCatalogueRepository(
            {world.id: world}
        ),
    )

    first = service.register_destination(
        world_id=world.id,
        telegram_chat_id="-100123",
        destination_type=TelegramDestinationType.GROUP,
    )

    assert first is not None

    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        service.register_destination(
            world_id=world.id,
            telegram_chat_id="-100123",
            destination_type=TelegramDestinationType.GROUP,
        )


def test_service_rejects_invalid_world_id():
    world = make_world()
    service = make_service(world)

    with pytest.raises(
        ValueError,
        match="world_id must be a UUID",
    ):
        service.register_destination(
            world_id="not-a-uuid",
            telegram_chat_id="-100123",
            destination_type=TelegramDestinationType.GROUP,
        )


def test_service_rejects_blank_chat_id():
    world = make_world()
    service = make_service(world)

    with pytest.raises(
        ValueError,
        match="telegram_chat_id is required",
    ):
        service.register_destination(
            world_id=world.id,
            telegram_chat_id="   ",
            destination_type=TelegramDestinationType.GROUP,
        )


def test_service_rejects_invalid_destination_type():
    world = make_world()
    service = make_service(world)

    with pytest.raises(
        ValueError,
        match="destination_type is invalid",
    ):
        service.register_destination(
            world_id=world.id,
            telegram_chat_id="-100123",
            destination_type="GROUP",
        )


def test_service_supports_channel_destination():
    world = make_world()
    service = make_service(world)

    destination = service.register_destination(
        world_id=world.id,
        telegram_chat_id="-100456",
        destination_type=TelegramDestinationType.CHANNEL,
    )

    assert destination.destination_type == TelegramDestinationType.CHANNEL


def test_service_lists_destinations_by_world():
    world = make_world()
    repository = FakeDestinationRepository()

    service = WorldTelegramDestinationService(
        repository=repository,
        world_catalogue_repository=FakeWorldCatalogueRepository(
            {world.id: world}
        ),
    )

    first = service.register_destination(
        world_id=world.id,
        telegram_chat_id="-100123",
        destination_type=TelegramDestinationType.GROUP,
    )

    second = service.register_destination(
        world_id=world.id,
        telegram_chat_id="-100456",
        destination_type=TelegramDestinationType.CHANNEL,
    )

    destinations = service.list_destinations(world.id)

    assert destinations == (first, second)


def test_service_can_enable_and_disable_destination():
    world = make_world()
    repository = FakeDestinationRepository()

    service = WorldTelegramDestinationService(
        repository=repository,
        world_catalogue_repository=FakeWorldCatalogueRepository(
            {world.id: world}
        ),
    )

    destination = service.register_destination(
        world_id=world.id,
        telegram_chat_id="-100123",
        destination_type=TelegramDestinationType.GROUP,
    )

    disabled = service.set_enabled(
        destination_id=destination.id,
        enabled=False,
    )

    assert disabled.enabled is False
    assert disabled.id == destination.id
    assert disabled.world_id == world.id

    enabled = service.set_enabled(
        destination_id=destination.id,
        enabled=True,
    )

    assert enabled.enabled is True
    assert enabled.id == destination.id


def test_service_rejects_enable_change_for_unknown_destination():
    world = make_world()
    service = make_service(world)

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        service.set_enabled(
            destination_id=uuid4(),
            enabled=False,
        )


def test_service_deletes_destination():
    world = make_world()
    repository = FakeDestinationRepository()

    service = WorldTelegramDestinationService(
        repository=repository,
        world_catalogue_repository=FakeWorldCatalogueRepository(
            {world.id: world}
        ),
    )

    destination = service.register_destination(
        world_id=world.id,
        telegram_chat_id="-100123",
        destination_type=TelegramDestinationType.GROUP,
    )

    assert service.delete_destination(destination.id) is True
    assert service.get_destination(destination.id) is None


def test_service_delete_unknown_destination_returns_false():
    world = make_world()
    service = make_service(world)

    assert service.delete_destination(uuid4()) is False


def test_domain_rejects_blank_chat_id():
    with pytest.raises(
        ValueError,
        match="telegram_chat_id",
    ):
        WorldTelegramDestination(
            id=uuid4(),
            world_id=uuid4(),
            telegram_chat_id=" ",
            destination_type=TelegramDestinationType.GROUP,
            enabled=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )