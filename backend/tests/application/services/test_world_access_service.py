from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import pytest

from app.application.services.world_access_service import (
    LearningWorldDisabledError,
    LearningWorldNotFoundError,
    UserNotFoundError,
    WorldAccessError,
    WorldAccessService,
)
from app.domain.learning.learner_world_access import (
    ACTIVE,
    BETA,
    LearnerWorldAccess,
)


class FakeUser:
    def __init__(self, user_id: UUID) -> None:
        self.id = user_id


class FakeUserIdentityReader:
    """Deterministic fake for the canonical user-identity boundary."""

    def __init__(self, users: set[UUID] | None = None) -> None:
        self.users = users or set()

    async def get_user_for_identity(
        self,
        user_id: UUID,
    ) -> FakeUser | None:
        if user_id not in self.users:
            return None

        return FakeUser(user_id)


class FakeWorld:
    def __init__(
        self,
        *,
        world_id: UUID,
        identifier: str = "french_world",
        enabled: bool = True,
    ) -> None:
        self.id = world_id
        self.identifier = identifier
        self.enabled = enabled


class FakeWorldRepository:
    def __init__(self, world: FakeWorld | None) -> None:
        self.world = world

    def get_by_identifier(
        self,
        identifier: str,
    ) -> FakeWorld | None:
        if self.world is None:
            return None

        if self.world.identifier != identifier:
            return None

        return self.world


class FakeAccessRepository:
    def __init__(self) -> None:
        self.records: dict[
            tuple[UUID, UUID],
            LearnerWorldAccess,
        ] = {}

    def save(
        self,
        access: LearnerWorldAccess,
    ) -> LearnerWorldAccess:
        self.records[
            (access.user_id, access.world_id)
        ] = access

        return access

    def get_by_id(
        self,
        access_id: UUID,
    ) -> LearnerWorldAccess | None:
        for access in self.records.values():
            if access.access_id == access_id:
                return access

        return None

    def get_by_user_and_world(
        self,
        *,
        user_id: UUID,
        world_id: UUID,
    ) -> LearnerWorldAccess | None:
        return self.records.get(
            (user_id, world_id)
        )

    def list_by_user(
        self,
        *,
        user_id: UUID,
    ) -> tuple[LearnerWorldAccess, ...]:
        return tuple(
            access
            for access in self.records.values()
            if access.user_id == user_id
        )


def run(awaitable):
    return asyncio.run(awaitable)


def create_service(
    *,
    user_id: UUID,
    access_repository: FakeAccessRepository | None = None,
    world: FakeWorld | None = None,
    user_exists: bool = True,
) -> tuple[
    WorldAccessService,
    FakeAccessRepository,
]:
    access_repository = (
        access_repository
        if access_repository is not None
        else FakeAccessRepository()
    )

    user_identity_reader = FakeUserIdentityReader(
        users={user_id} if user_exists else set()
    )

    service = WorldAccessService(
        access_repository=access_repository,
        user_identity_reader=user_identity_reader,
        learning_world_repository=FakeWorldRepository(world),
    )

    return service, access_repository


def test_grant_access_creates_active_beta_access() -> None:
    user_id = uuid4()
    world_id = uuid4()

    service, access_repository = create_service(
        user_id=user_id,
        world=FakeWorld(
            world_id=world_id,
        ),
    )

    access = run(
        service.grant_access(
            user_id=user_id,
            world_identifier="french_world",
        )
    )

    assert access.user_id == user_id
    assert access.world_id == world_id
    assert access.status == ACTIVE
    assert access.access_source == BETA
    assert access.is_active() is True

    stored = access_repository.get_by_user_and_world(
        user_id=user_id,
        world_id=world_id,
    )

    assert stored is not None
    assert stored.access_id == access.access_id


def test_grant_access_is_idempotent_for_existing_active_access() -> None:
    user_id = uuid4()
    world_id = uuid4()

    access_repository = FakeAccessRepository()

    service, _ = create_service(
        user_id=user_id,
        access_repository=access_repository,
        world=FakeWorld(
            world_id=world_id,
        ),
    )

    first = run(
        service.grant_access(
            user_id=user_id,
            world_identifier="french_world",
        )
    )

    second = run(
        service.grant_access(
            user_id=user_id,
            world_identifier="french_world",
        )
    )

    assert second.access_id == first.access_id
    assert second.user_id == user_id
    assert second.world_id == world_id
    assert second.status == ACTIVE

    assert len(access_repository.records) == 1


def test_grant_access_reactivates_revoked_access() -> None:
    user_id = uuid4()
    world_id = uuid4()

    access_repository = FakeAccessRepository()

    revoked = LearnerWorldAccess.grant(
        user_id=user_id,
        world_id=world_id,
        access_source=BETA,
    ).revoke()

    access_repository.save(revoked)

    service, _ = create_service(
        user_id=user_id,
        access_repository=access_repository,
        world=FakeWorld(
            world_id=world_id,
        ),
    )

    restored = run(
        service.grant_access(
            user_id=user_id,
            world_identifier="french_world",
        )
    )

    assert restored.access_id == revoked.access_id
    assert restored.user_id == user_id
    assert restored.world_id == world_id
    assert restored.status == ACTIVE
    assert restored.access_source == BETA
    assert restored.is_active() is True


def test_grant_access_rejects_missing_user() -> None:
    user_id = uuid4()
    world_id = uuid4()

    service, _ = create_service(
        user_id=user_id,
        user_exists=False,
        world=FakeWorld(
            world_id=world_id,
        ),
    )

    with pytest.raises(
        UserNotFoundError,
        match="Canonical user does not exist",
    ):
        run(
            service.grant_access(
                user_id=user_id,
                world_identifier="french_world",
            )
        )


def test_grant_access_rejects_missing_world() -> None:
    user_id = uuid4()

    service, _ = create_service(
        user_id=user_id,
        world=None,
    )

    with pytest.raises(
        LearningWorldNotFoundError,
        match="Learning World does not exist",
    ):
        run(
            service.grant_access(
                user_id=user_id,
                world_identifier="french_world",
            )
        )


def test_grant_access_rejects_disabled_world() -> None:
    user_id = uuid4()
    world_id = uuid4()

    service, _ = create_service(
        user_id=user_id,
        world=FakeWorld(
            world_id=world_id,
            enabled=False,
        ),
    )

    with pytest.raises(
        LearningWorldDisabledError,
        match="Learning World is disabled",
    ):
        run(
            service.grant_access(
                user_id=user_id,
                world_identifier="french_world",
            )
        )


def test_grant_access_rejects_non_uuid_user_id() -> None:
    service, _ = create_service(
        user_id=uuid4(),
        world=FakeWorld(
            world_id=uuid4(),
        ),
    )

    with pytest.raises(
        ValueError,
        match="user_id must be a UUID",
    ):
        run(
            service.grant_access(
                user_id="not-a-uuid",
                world_identifier="french_world",
            )
        )


def test_get_access_returns_existing_access() -> None:
    user_id = uuid4()
    world_id = uuid4()

    access_repository = FakeAccessRepository()

    access = LearnerWorldAccess.grant(
        user_id=user_id,
        world_id=world_id,
        access_source=BETA,
    )

    access_repository.save(access)

    service, _ = create_service(
        user_id=user_id,
        access_repository=access_repository,
        world=FakeWorld(
            world_id=world_id,
        ),
    )

    result = run(
        service.get_access(
            user_id=user_id,
            world_identifier="french_world",
        )
    )

    assert result is not None
    assert result.access_id == access.access_id


def test_get_access_returns_none_for_unknown_world() -> None:
    user_id = uuid4()

    service, _ = create_service(
        user_id=user_id,
        world=None,
    )

    result = run(
        service.get_access(
            user_id=user_id,
            world_identifier="french_world",
        )
    )

    assert result is None


def test_has_access_returns_true_for_active_access() -> None:
    user_id = uuid4()
    world_id = uuid4()

    service, _ = create_service(
        user_id=user_id,
        world=FakeWorld(
            world_id=world_id,
        ),
    )

    run(
        service.grant_access(
            user_id=user_id,
            world_identifier="french_world",
        )
    )

    assert run(
        service.has_access(
            user_id=user_id,
            world_identifier="french_world",
        )
    ) is True


def test_has_access_returns_false_without_access() -> None:
    user_id = uuid4()
    world_id = uuid4()

    service, _ = create_service(
        user_id=user_id,
        world=FakeWorld(
            world_id=world_id,
        ),
    )

    assert run(
        service.has_access(
            user_id=user_id,
            world_identifier="french_world",
        )
    ) is False


def test_require_access_returns_active_access() -> None:
    user_id = uuid4()
    world_id = uuid4()

    service, _ = create_service(
        user_id=user_id,
        world=FakeWorld(
            world_id=world_id,
        ),
    )

    created = run(
        service.grant_access(
            user_id=user_id,
            world_identifier="french_world",
        )
    )

    result = run(
        service.require_access(
            user_id=user_id,
            world_identifier="french_world",
        )
    )

    assert result.access_id == created.access_id
    assert result.status == ACTIVE


def test_require_access_rejects_missing_access() -> None:
    user_id = uuid4()
    world_id = uuid4()

    service, _ = create_service(
        user_id=user_id,
        world=FakeWorld(
            world_id=world_id,
        ),
    )

    with pytest.raises(
        PermissionError,
        match="does not have active access",
    ):
        run(
            service.require_access(
                user_id=user_id,
                world_identifier="french_world",
            )
        )


def test_list_world_access_returns_user_access_only() -> None:
    user_id = uuid4()
    other_user_id = uuid4()

    world_id = uuid4()
    other_world_id = uuid4()

    access_repository = FakeAccessRepository()

    own_access = LearnerWorldAccess.grant(
        user_id=user_id,
        world_id=world_id,
        access_source=BETA,
    )

    other_access = LearnerWorldAccess.grant(
        user_id=other_user_id,
        world_id=other_world_id,
        access_source=BETA,
    )

    access_repository.save(own_access)
    access_repository.save(other_access)

    service, _ = create_service(
        user_id=user_id,
        access_repository=access_repository,
        world=FakeWorld(
            world_id=world_id,
        ),
    )

    result = run(
        service.list_world_access(
            user_id=user_id,
        )
    )

    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0].access_id == own_access.access_id
    assert result[0].user_id == user_id
    assert result[0].world_id == world_id
