"""Focused tests for WorldAccessService access revocation."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.application.services.world_access_service import (
    LearningWorldNotFoundError,
    WorldAccessService,
)
from app.domain.learning.learner_world_access import LearnerWorldAccess


class FakeAccessRepository:
    def __init__(self) -> None:
        self.records: dict[tuple[object, object], LearnerWorldAccess] = {}

    def get_by_user_and_world(
        self,
        *,
        user_id,
        world_id,
    ):
        return self.records.get((user_id, world_id))

    def save(self, access: LearnerWorldAccess) -> LearnerWorldAccess:
        self.records[(access.user_id, access.world_id)] = access
        return access

    def list_by_user(self, *, user_id):
        return tuple(
            access
            for (record_user_id, _), access in self.records.items()
            if record_user_id == user_id
        )


class FakeUserIdentityReader:
    def get_user_for_identity(self, user_id):
        return SimpleNamespace(id=user_id)


class FakeLearningWorldRepository:
    def __init__(self, world):
        self.world = world

    def get_by_identifier(self, identifier: str):
        if self.world is None:
            return None

        if self.world.identifier != identifier:
            return None

        return self.world


def build_service(
    *,
    world,
):
    return WorldAccessService(
        access_repository=FakeAccessRepository(),
        user_identity_reader=FakeUserIdentityReader(),
        learning_world_repository=FakeLearningWorldRepository(world),
    )


@pytest.mark.asyncio
async def test_revoke_access_revokes_active_access() -> None:
    user_id = uuid4()
    world_id = uuid4()

    world = SimpleNamespace(
        id=world_id,
        identifier="french",
        enabled=True,
    )

    service = build_service(world=world)

    granted = await service.grant_access(
        user_id=user_id,
        world_identifier="french",
        access_source="subscription",
    )

    revoked = await service.revoke_access(
        user_id=user_id,
        world_identifier="french",
        access_source="subscription",
    )

    assert granted.is_active()
    assert revoked is not None
    assert not revoked.is_active()
    assert revoked.access_source == "subscription"


@pytest.mark.asyncio
async def test_revoke_access_is_idempotent() -> None:
    user_id = uuid4()
    world_id = uuid4()

    world = SimpleNamespace(
        id=world_id,
        identifier="french",
        enabled=True,
    )

    service = build_service(world=world)

    await service.grant_access(
        user_id=user_id,
        world_identifier="french",
        access_source="subscription",
    )

    first_revoke = await service.revoke_access(
        user_id=user_id,
        world_identifier="french",
        access_source="subscription",
    )

    second_revoke = await service.revoke_access(
        user_id=user_id,
        world_identifier="french",
        access_source="subscription",
    )

    assert first_revoke is not None
    assert second_revoke is not None
    assert second_revoke.access_id == first_revoke.access_id
    assert not second_revoke.is_active()


@pytest.mark.asyncio
async def test_revoke_access_does_not_revoke_different_access_source() -> None:
    user_id = uuid4()
    world_id = uuid4()

    world = SimpleNamespace(
        id=world_id,
        identifier="french",
        enabled=True,
    )

    service = build_service(world=world)

    granted = await service.grant_access(
        user_id=user_id,
        world_identifier="french",
        access_source="beta",
    )

    result = await service.revoke_access(
        user_id=user_id,
        world_identifier="french",
        access_source="subscription",
    )

    assert result is not None
    assert result.access_id == granted.access_id
    assert result.access_source == "beta"
    assert result.is_active()


@pytest.mark.asyncio
async def test_revoke_access_without_existing_access_returns_none() -> None:
    user_id = uuid4()
    world_id = uuid4()

    world = SimpleNamespace(
        id=world_id,
        identifier="french",
        enabled=True,
    )

    service = build_service(world=world)

    result = await service.revoke_access(
        user_id=user_id,
        world_identifier="french",
        access_source="subscription",
    )

    assert result is None


@pytest.mark.asyncio
async def test_revoke_access_unknown_world_fails() -> None:
    user_id = uuid4()

    service = build_service(world=None)

    with pytest.raises(LearningWorldNotFoundError):
        await service.revoke_access(
            user_id=user_id,
            world_identifier="does-not-exist",
            access_source="subscription",
        )