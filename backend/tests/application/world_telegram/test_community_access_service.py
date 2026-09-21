"""Unit tests for WorldTelegramCommunityAccessService."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.application.world_telegram.community_access_service import (
    WorldTelegramCommunityAccessService,
    WorldTelegramDestinationDisabledError,
    WorldTelegramDestinationNotFoundError,
)
from app.domain.world_telegram import (
    TelegramDestinationType,
    TelegramMembershipStatus,
    WorldTelegramDestination,
    WorldTelegramMembership,
)


class FakeWorldAccessService:
    def __init__(self, access=None):
        self.access = access
        self.get_access_calls = []

    def get_access(self, *, user_id, world_identifier):
        self.get_access_calls.append(
            {
                "user_id": user_id,
                "world_identifier": world_identifier,
            }
        )
        return self.access


class FakeWorldCatalogueRepository:
    def __init__(self):
        self.items = {}

    def get_by_id(self, world_id):
        return self.items.get(world_id)

    def get_by_identifier(self, identifier):
        return next(
            (
                item
                for item in self.items.values()
                if item.identifier == identifier
            ),
            None,
        )

    def list_all(self):
        return tuple(self.items.values())


class FakeDestinationRepository:
    def __init__(self):
        self.items = {}

    def get_by_id(self, destination_id):
        return self.items.get(destination_id)

    def get_by_world_and_chat(
        self,
        *,
        world_id,
        telegram_chat_id,
    ):
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


class FakeMembershipService:
    def __init__(self):
        self.memberships = {}
        self.get_calls = []
        self.register_calls = []
        self.set_active_calls = []

    def get_membership_for_user(
        self,
        *,
        destination_id,
        user_id,
    ):
        self.get_calls.append(
            {
                "destination_id": destination_id,
                "user_id": user_id,
            }
        )

        return next(
            (
                membership
                for membership in self.memberships.values()
                if membership.destination_id == destination_id
                and membership.user_id == user_id
            ),
            None,
        )

    def register_membership(
        self,
        *,
        destination_id,
        user_id,
    ):
        self.register_calls.append(
            {
                "destination_id": destination_id,
                "user_id": user_id,
            }
        )

        now = datetime.now(timezone.utc)

        membership = WorldTelegramMembership(
            id=uuid4(),
            destination_id=destination_id,
            user_id=user_id,
            status=TelegramMembershipStatus.ACTIVE,
            joined_at=now,
            left_at=None,
            created_at=now,
            updated_at=now,
        )

        self.memberships[membership.id] = membership
        return membership

    def set_active(
        self,
        *,
        membership_id,
        active,
    ):
        self.set_active_calls.append(
            {
                "membership_id": membership_id,
                "active": active,
            }
        )

        membership = self.memberships[membership_id]
        now = datetime.now(timezone.utc)

        updated = WorldTelegramMembership(
            id=membership.id,
            destination_id=membership.destination_id,
            user_id=membership.user_id,
            status=(
                TelegramMembershipStatus.ACTIVE
                if active
                else TelegramMembershipStatus.INACTIVE
            ),
            joined_at=membership.joined_at,
            left_at=None if active else now,
            created_at=membership.created_at,
            updated_at=now,
        )

        self.memberships[membership.id] = updated
        return updated


def make_world(world_id=None, identifier="french"):
    if world_id is None:
        world_id = uuid4()

    return SimpleNamespace(
        id=world_id,
        identifier=identifier,
        enabled=True,
    )


def make_destination(world_id, *, enabled=True):
    now = datetime.now(timezone.utc)

    return WorldTelegramDestination(
        id=uuid4(),
        world_id=world_id,
        telegram_chat_id=f"-100{uuid4().int % 100000000}",
        destination_type=TelegramDestinationType.GROUP,
        enabled=enabled,
        created_at=now,
        updated_at=now,
    )


def make_active_access():
    return SimpleNamespace(
        is_active=lambda: True,
    )


def make_inactive_access():
    return SimpleNamespace(
        is_active=lambda: False,
    )


def make_service(
    *,
    world=None,
    access=None,
    destination=None,
):
    catalogue = FakeWorldCatalogueRepository()

    if world is not None:
        catalogue.items[world.id] = world

    destinations = FakeDestinationRepository()

    if destination is not None:
        destinations.save(destination)

    world_access = FakeWorldAccessService(access=access)
    membership_service = FakeMembershipService()

    service = WorldTelegramCommunityAccessService(
        world_access_service=world_access,
        world_catalogue_repository=catalogue,
        destination_repository=destinations,
        membership_service=membership_service,
    )

    return (
        service,
        world_access,
        catalogue,
        destinations,
        membership_service,
    )


def test_rejects_unknown_world():
    service, world_access, _, _, _ = make_service(
        access=make_active_access(),
    )

    with pytest.raises(ValueError, match="does not exist"):
        service.ensure_membership(
            user_id=uuid4(),
            world_id=uuid4(),
        )

    assert world_access.get_access_calls == []


def test_rejects_learner_without_world_access():
    world = make_world()

    service, world_access, _, _, membership_service = make_service(
        world=world,
        access=None,
    )

    with pytest.raises(
        PermissionError,
        match="does not have active access",
    ):
        service.ensure_membership(
            user_id=uuid4(),
            world_id=world.id,
        )

    assert len(world_access.get_access_calls) == 1
    assert membership_service.register_calls == []


def test_rejects_inactive_world_access():
    world = make_world()

    service, world_access, _, _, membership_service = make_service(
        world=world,
        access=make_inactive_access(),
    )

    with pytest.raises(
        PermissionError,
        match="does not have active access",
    ):
        service.ensure_membership(
            user_id=uuid4(),
            world_id=world.id,
        )

    assert len(world_access.get_access_calls) == 1
    assert membership_service.register_calls == []


def test_resolves_world_id_to_catalogue_identifier_before_access_check():
    world = make_world(identifier="french-b1")
    destination = make_destination(world.id)
    user_id = uuid4()

    service, world_access, _, _, _ = make_service(
        world=world,
        access=make_active_access(),
        destination=destination,
    )

    service.ensure_membership(
        user_id=user_id,
        world_id=world.id,
    )

    assert world_access.get_access_calls == [
        {
            "user_id": user_id,
            "world_identifier": "french-b1",
        }
    ]


def test_rejects_when_world_has_no_telegram_destination():
    world = make_world()

    service, _, _, _, membership_service = make_service(
        world=world,
        access=make_active_access(),
    )

    with pytest.raises(
        WorldTelegramDestinationNotFoundError,
        match="No Telegram destination is registered",
    ):
        service.ensure_membership(
            user_id=uuid4(),
            world_id=world.id,
        )

    assert membership_service.register_calls == []


def test_rejects_when_all_telegram_destinations_are_disabled():
    world = make_world()
    destination = make_destination(
        world.id,
        enabled=False,
    )

    service, _, _, _, membership_service = make_service(
        world=world,
        access=make_active_access(),
        destination=destination,
    )

    with pytest.raises(
        WorldTelegramDestinationDisabledError,
        match="All Telegram destinations",
    ):
        service.ensure_membership(
            user_id=uuid4(),
            world_id=world.id,
        )

    assert membership_service.register_calls == []


def test_registers_first_membership_for_eligible_learner():
    world = make_world()
    destination = make_destination(world.id)
    user_id = uuid4()

    service, _, _, _, membership_service = make_service(
        world=world,
        access=make_active_access(),
        destination=destination,
    )

    membership = service.ensure_membership(
        user_id=user_id,
        world_id=world.id,
    )

    assert membership.destination_id == destination.id
    assert membership.user_id == user_id
    assert membership.status is TelegramMembershipStatus.ACTIVE

    assert membership_service.register_calls == [
        {
            "destination_id": destination.id,
            "user_id": user_id,
        }
    ]


def test_existing_active_membership_is_idempotent():
    world = make_world()
    destination = make_destination(world.id)
    user_id = uuid4()

    service, _, _, _, membership_service = make_service(
        world=world,
        access=make_active_access(),
        destination=destination,
    )

    existing = membership_service.register_membership(
        destination_id=destination.id,
        user_id=user_id,
    )

    result = service.ensure_membership(
        user_id=user_id,
        world_id=world.id,
    )

    assert result == existing

    assert membership_service.register_calls == [
        {
            "destination_id": destination.id,
            "user_id": user_id,
        }
    ]

    assert membership_service.set_active_calls == []


def test_existing_inactive_membership_is_reactivated():
    world = make_world()
    destination = make_destination(world.id)
    user_id = uuid4()

    service, _, _, _, membership_service = make_service(
        world=world,
        access=make_active_access(),
        destination=destination,
    )

    existing = membership_service.register_membership(
        destination_id=destination.id,
        user_id=user_id,
    )

    membership_service.set_active(
        membership_id=existing.id,
        active=False,
    )

    result = service.ensure_membership(
        user_id=user_id,
        world_id=world.id,
    )

    assert result.id == existing.id
    assert result.status is TelegramMembershipStatus.ACTIVE
    assert result.left_at is None

    assert membership_service.set_active_calls[-1] == {
        "membership_id": existing.id,
        "active": True,
    }


def test_does_not_grant_world_access():
    world = make_world()
    destination = make_destination(world.id)
    user_id = uuid4()

    service, world_access, _, _, _ = make_service(
        world=world,
        access=make_active_access(),
        destination=destination,
    )

    assert not hasattr(world_access, "grant_access")

    service.ensure_membership(
        user_id=user_id,
        world_id=world.id,
    )

    assert len(world_access.get_access_calls) == 1


def test_requires_uuid_inputs():
    world = make_world()

    service, _, _, _, _ = make_service(
        world=world,
        access=make_active_access(),
    )

    with pytest.raises(ValueError, match="user_id must be a UUID"):
        service.ensure_membership(
            user_id="not-a-uuid",
            world_id=world.id,
        )

    with pytest.raises(ValueError, match="world_id must be a UUID"):
        service.ensure_membership(
            user_id=uuid4(),
            world_id="not-a-uuid",
        )