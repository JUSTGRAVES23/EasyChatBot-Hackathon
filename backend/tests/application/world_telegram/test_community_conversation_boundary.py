from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.application.world_telegram.community_conversation_boundary import (
    WorldTelegramCommunityChatTypeError,
    WorldTelegramCommunityConversationBoundary,
    WorldTelegramCommunityDestinationDisabledError,
    WorldTelegramCommunityDestinationNotFoundError,
)
from app.domain.world_telegram import (
    TelegramDestinationType,
    TelegramMembershipStatus,
    WorldTelegramDestination,
    WorldTelegramMembership,
)


@dataclass
class FakeAccess:
    active: bool = True

    def is_active(self) -> bool:
        return self.active


class FakeWorldCatalogue:
    def __init__(self, world):
        self.world = world
        self.calls = []

    def get_by_id(self, world_id):
        self.calls.append(world_id)
        return self.world


class FakeWorldAccess:
    def __init__(self, access):
        self.access = access
        self.calls = []

    def get_access(self, *, user_id, world_identifier):
        self.calls.append((user_id, world_identifier))
        return self.access


class FakeDestinationRepository:
    def __init__(self, destination):
        self.destination = destination
        self.calls = []

    def get_by_world_and_chat(self, *, world_id, telegram_chat_id):
        self.calls.append((world_id, telegram_chat_id))
        return self.destination


class FakeMembershipService:
    def __init__(self, membership):
        self.membership = membership
        self.calls = []

    def get_membership_for_user(self, *, destination_id, user_id):
        self.calls.append((destination_id, user_id))
        return self.membership


def make_boundary(*, world=None, access=None, destination=None, membership=None):
    world_catalogue = FakeWorldCatalogue(world)
    world_access = FakeWorldAccess(access)
    destinations = FakeDestinationRepository(destination)
    memberships = FakeMembershipService(membership)

    boundary = WorldTelegramCommunityConversationBoundary(
        world_access_service=world_access,
        world_catalogue_repository=world_catalogue,
        destination_repository=destinations,
        membership_service=memberships,
    )

    return boundary, world_catalogue, world_access, destinations, memberships


def make_world():
    return SimpleNamespace(id=uuid4(), identifier="french-b1")


def make_destination(world_id):
    return WorldTelegramDestination(
        id=uuid4(),
        world_id=world_id,
        telegram_chat_id="-100123456789",
        destination_type=TelegramDestinationType.GROUP,
        enabled=True,
        created_at=SimpleNamespace(),
        updated_at=SimpleNamespace(),
    )


def make_membership(destination_id, user_id, status=TelegramMembershipStatus.ACTIVE):
    return WorldTelegramMembership(
        id=uuid4(),
        destination_id=destination_id,
        user_id=user_id,
        status=status,
        joined_at=SimpleNamespace(),
        left_at=None,
        created_at=SimpleNamespace(),
        updated_at=SimpleNamespace(),
    )


def test_private_chat_is_rejected():
    world = make_world()
    boundary, *_ = make_boundary(world=world, access=FakeAccess())

    with pytest.raises(WorldTelegramCommunityChatTypeError):
        boundary.authorize_message(
            user_id=uuid4(),
            world_id=world.id,
            telegram_chat_id="-100123456789",
            chat_type="private",
            message="Hello",
        )


def test_channel_destination_is_not_accepted():
    world = make_world()
    destination = WorldTelegramDestination(
        id=uuid4(),
        world_id=world.id,
        telegram_chat_id="-100123456789",
        destination_type=TelegramDestinationType.CHANNEL,
        enabled=True,
        created_at=SimpleNamespace(),
        updated_at=SimpleNamespace(),
    )

    boundary, *_ = make_boundary(
        world=world,
        access=FakeAccess(),
        destination=destination,
    )

    with pytest.raises(WorldTelegramCommunityChatTypeError):
        boundary.authorize_message(
            user_id=uuid4(),
            world_id=world.id,
            telegram_chat_id="-100123456789",
            chat_type="group",
            message="Hello",
        )


def test_unknown_world_is_rejected():
    boundary, *_ = make_boundary(world=None, access=FakeAccess())

    with pytest.raises(ValueError, match="does not exist"):
        boundary.authorize_message(
            user_id=uuid4(),
            world_id=uuid4(),
            telegram_chat_id="-100123456789",
            chat_type="group",
            message="Hello",
        )


def test_unregistered_group_is_rejected():
    world = make_world()
    boundary, *_ = make_boundary(
        world=world,
        access=FakeAccess(),
        destination=None,
    )

    with pytest.raises(WorldTelegramCommunityDestinationNotFoundError):
        boundary.authorize_message(
            user_id=uuid4(),
            world_id=world.id,
            telegram_chat_id="-100123456789",
            chat_type="group",
            message="Hello",
        )


def test_disabled_group_is_rejected():
    world = make_world()
    destination = make_destination(world.id)
    destination = WorldTelegramDestination(
        id=destination.id,
        world_id=destination.world_id,
        telegram_chat_id=destination.telegram_chat_id,
        destination_type=destination.destination_type,
        enabled=False,
        created_at=destination.created_at,
        updated_at=destination.updated_at,
    )

    boundary, *_ = make_boundary(
        world=world,
        access=FakeAccess(),
        destination=destination,
    )

    with pytest.raises(WorldTelegramCommunityDestinationDisabledError):
        boundary.authorize_message(
            user_id=uuid4(),
            world_id=world.id,
            telegram_chat_id=destination.telegram_chat_id,
            chat_type="group",
            message="Hello",
        )


def test_missing_world_access_is_rejected():
    world = make_world()
    destination = make_destination(world.id)

    boundary, *_ = make_boundary(
        world=world,
        access=None,
        destination=destination,
    )

    with pytest.raises(PermissionError, match="active access"):
        boundary.authorize_message(
            user_id=uuid4(),
            world_id=world.id,
            telegram_chat_id=destination.telegram_chat_id,
            chat_type="group",
            message="Hello",
        )


def test_inactive_world_access_is_rejected():
    world = make_world()
    destination = make_destination(world.id)

    boundary, *_ = make_boundary(
        world=world,
        access=FakeAccess(active=False),
        destination=destination,
    )

    with pytest.raises(PermissionError, match="active access"):
        boundary.authorize_message(
            user_id=uuid4(),
            world_id=world.id,
            telegram_chat_id=destination.telegram_chat_id,
            chat_type="group",
            message="Hello",
        )


def test_missing_membership_is_rejected():
    world = make_world()
    destination = make_destination(world.id)

    boundary, *_ = make_boundary(
        world=world,
        access=FakeAccess(),
        destination=destination,
        membership=None,
    )

    with pytest.raises(PermissionError, match="active membership"):
        boundary.authorize_message(
            user_id=uuid4(),
            world_id=world.id,
            telegram_chat_id=destination.telegram_chat_id,
            chat_type="group",
            message="Hello",
        )


def test_inactive_membership_is_rejected():
    world = make_world()
    user_id = uuid4()
    destination = make_destination(world.id)
    membership = make_membership(
        destination.id,
        user_id,
        TelegramMembershipStatus.INACTIVE,
    )

    boundary, *_ = make_boundary(
        world=world,
        access=FakeAccess(),
        destination=destination,
        membership=membership,
    )

    with pytest.raises(PermissionError, match="active membership"):
        boundary.authorize_message(
            user_id=user_id,
            world_id=world.id,
            telegram_chat_id=destination.telegram_chat_id,
            chat_type="supergroup",
            message="Hello",
        )


def test_authorizes_registered_group_for_entitled_member():
    world = make_world()
    user_id = uuid4()
    destination = make_destination(world.id)
    membership = make_membership(destination.id, user_id)

    (
        boundary,
        world_catalogue,
        world_access,
        destinations,
        memberships,
    ) = make_boundary(
        world=world,
        access=FakeAccess(),
        destination=destination,
        membership=membership,
    )

    context = boundary.authorize_message(
        user_id=user_id,
        world_id=world.id,
        telegram_chat_id="  -100123456789  ",
        chat_type="supergroup",
        message="  Hello community  ",
    )

    assert context.user_id == user_id
    assert context.world_id == world.id
    assert context.destination_id == destination.id
    assert context.telegram_chat_id == "-100123456789"
    assert context.message == "Hello community"

    assert world_catalogue.calls == [world.id]
    assert world_access.calls == [(user_id, world.identifier)]
    assert destinations.calls == [(world.id, "-100123456789")]
    assert memberships.calls == [(destination.id, user_id)]


@pytest.mark.parametrize("chat_type", ["private", "channel", None, ""])
def test_only_group_chat_types_are_supported(chat_type):
    world = make_world()
    boundary, *_ = make_boundary(world=world, access=FakeAccess())

    with pytest.raises(WorldTelegramCommunityChatTypeError):
        boundary.authorize_message(
            user_id=uuid4(),
            world_id=world.id,
            telegram_chat_id="-100123456789",
            chat_type=chat_type,
            message="Hello",
        )


def test_empty_message_is_rejected():
    world = make_world()
    boundary, *_ = make_boundary(world=world, access=FakeAccess())

    with pytest.raises(ValueError, match="empty"):
        boundary.authorize_message(
            user_id=uuid4(),
            world_id=world.id,
            telegram_chat_id="-100123456789",
            chat_type="group",
            message="   ",
        )


def test_message_over_telegram_limit_is_rejected():
    world = make_world()
    boundary, *_ = make_boundary(world=world, access=FakeAccess())

    with pytest.raises(ValueError, match="Telegram community message limit"):
        boundary.authorize_message(
            user_id=uuid4(),
            world_id=world.id,
            telegram_chat_id="-100123456789",
            chat_type="group",
            message="x" * 4097,
        )
