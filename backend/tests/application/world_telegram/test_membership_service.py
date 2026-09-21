"""Unit tests for WorldTelegramMembershipService."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.world_telegram.membership_service import (
    WorldTelegramMembershipService,
)
from app.domain.world_telegram import (
    TelegramDestinationType,
    TelegramMembershipStatus,
    WorldTelegramDestination,
)


class FakeDestinationRepository:
    def __init__(self):
        self.items = {}

    def get_by_id(self, destination_id):
        return self.items.get(destination_id)

    def get_by_world_and_chat(self, *, world_id, telegram_chat_id):
        return None

    def list_by_world(self, world_id):
        return ()

    def save(self, destination):
        self.items[destination.id] = destination
        return destination

    def delete(self, destination_id):
        return self.items.pop(destination_id, None) is not None


class FakeMembershipRepository:
    def __init__(self):
        self.items = {}

    def get_by_id(self, membership_id):
        return self.items.get(membership_id)

    def get_by_destination_and_user(self, *, destination_id, user_id):
        return next(
            (
                item
                for item in self.items.values()
                if item.destination_id == destination_id
                and item.user_id == user_id
            ),
            None,
        )

    def list_by_destination(self, destination_id):
        return tuple(
            item
            for item in self.items.values()
            if item.destination_id == destination_id
        )

    def save(self, membership):
        self.items[membership.id] = membership
        return membership

    def delete(self, membership_id):
        return self.items.pop(membership_id, None) is not None


def make_destination():
    now = datetime.now(timezone.utc)

    return WorldTelegramDestination(
        id=uuid4(),
        world_id=uuid4(),
        telegram_chat_id="-100123",
        destination_type=TelegramDestinationType.GROUP,
        enabled=True,
        created_at=now,
        updated_at=now,
    )


def make_service(destination):
    destinations = FakeDestinationRepository()
    destinations.save(destination)

    return WorldTelegramMembershipService(
        repository=FakeMembershipRepository(),
        destination_repository=destinations,
    )


def test_registers_membership_for_registered_destination():
    destination = make_destination()
    service = make_service(destination)
    user_id = uuid4()

    membership = service.register_membership(
        destination_id=destination.id,
        user_id=user_id,
    )

    assert membership.destination_id == destination.id
    assert membership.user_id == user_id
    assert membership.status is TelegramMembershipStatus.ACTIVE
    assert membership.left_at is None


def test_rejects_unknown_destination():
    service = WorldTelegramMembershipService(
        repository=FakeMembershipRepository(),
        destination_repository=FakeDestinationRepository(),
    )

    with pytest.raises(ValueError, match="does not exist"):
        service.register_membership(
            destination_id=uuid4(),
            user_id=uuid4(),
        )


def test_rejects_duplicate_membership():
    destination = make_destination()
    service = make_service(destination)
    user_id = uuid4()

    service.register_membership(
        destination_id=destination.id,
        user_id=user_id,
    )

    with pytest.raises(ValueError, match="already registered"):
        service.register_membership(
            destination_id=destination.id,
            user_id=user_id,
        )


def test_gets_membership_for_user_and_destination():
    destination = make_destination()
    service = make_service(destination)
    user_id = uuid4()

    membership = service.register_membership(
        destination_id=destination.id,
        user_id=user_id,
    )

    result = service.get_membership_for_user(
        destination_id=destination.id,
        user_id=user_id,
    )

    assert result == membership
    assert result is not None
    assert result.id == membership.id


def test_returns_none_when_membership_for_user_does_not_exist():
    destination = make_destination()
    service = make_service(destination)

    result = service.get_membership_for_user(
        destination_id=destination.id,
        user_id=uuid4(),
    )

    assert result is None


def test_can_deactivate_and_reactivate_membership():
    destination = make_destination()
    service = make_service(destination)

    membership = service.register_membership(
        destination_id=destination.id,
        user_id=uuid4(),
    )

    inactive = service.set_active(
        membership_id=membership.id,
        active=False,
    )

    assert inactive.status is TelegramMembershipStatus.INACTIVE
    assert inactive.left_at is not None

    active = service.set_active(
        membership_id=membership.id,
        active=True,
    )

    assert active.status is TelegramMembershipStatus.ACTIVE
    assert active.left_at is None


def test_lists_memberships():
    destination = make_destination()
    service = make_service(destination)

    first = service.register_membership(
        destination_id=destination.id,
        user_id=uuid4(),
    )
    second = service.register_membership(
        destination_id=destination.id,
        user_id=uuid4(),
    )

    assert service.list_memberships(destination.id) == (first, second)


def test_deletes_membership():
    destination = make_destination()
    service = make_service(destination)

    membership = service.register_membership(
        destination_id=destination.id,
        user_id=uuid4(),
    )

    assert service.delete_membership(membership.id) is True
    assert service.get_membership(membership.id) is None