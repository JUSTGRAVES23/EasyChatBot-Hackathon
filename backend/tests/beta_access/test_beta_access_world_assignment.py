from __future__ import annotations

from pathlib import Path

import pytest

from app.application.beta_access.beta_access_service import (
    BetaAccessService,
)
from app.application.beta_access.models import BetaUserState
from app.application.uai.world.world_resolver import WorldResolver
from app.infrastructure.persistence.in_memory_beta_access_repository import (
    InMemoryBetaTokenRepository,
    InMemoryBetaUserRepository,
    InMemoryTelegramBindingRepository,
)
from app.infrastructure.worlds.yaml_world_repository import (
    YamlWorldRepository,
)


def create_world_resolver() -> WorldResolver:
    app_root = (
        Path(__file__)
        .resolve()
        .parents[2]
        / "app"
    )

    return WorldResolver(
        world_repository=YamlWorldRepository(
            worlds_path=(
                app_root
                / "configuration"
                / "worlds"
            )
        )
    )


def create_service(
    users: InMemoryBetaUserRepository,
) -> BetaAccessService:
    return BetaAccessService(
        user_repository=users,
        token_repository=InMemoryBetaTokenRepository(),
        binding_repository=InMemoryTelegramBindingRepository(),
        world_resolver=create_world_resolver(),
    )


@pytest.mark.asyncio
async def test_assign_world_persists_authoritative_world_id():
    users = InMemoryBetaUserRepository()

    await users.save(
        BetaUserState(
            user_id="david",
            email="david@example.com",
            email_verified=True,
            beta_approved=True,
            active_world_id=None,
        )
    )

    service = create_service(users)

    updated = await service.assign_world(
        user_id="david",
        world_id="french_world",
    )

    assert updated.active_world_id == "french_world"

    persisted = await users.get("david")

    assert persisted is not None
    assert persisted.active_world_id == "french_world"


@pytest.mark.asyncio
async def test_assign_world_canonicalizes_legacy_world_id():
    users = InMemoryBetaUserRepository()

    await users.save(
        BetaUserState(
            user_id="david",
            email="david@example.com",
            email_verified=True,
            beta_approved=True,
            active_world_id=None,
        )
    )

    service = create_service(users)

    updated = await service.assign_world(
        user_id="david",
        world_id="world-fr",
    )

    assert updated.active_world_id == "french_world"

    persisted = await users.get("david")

    assert persisted is not None
    assert persisted.active_world_id == "french_world"


@pytest.mark.asyncio
async def test_assign_world_rejects_unknown_world():
    users = InMemoryBetaUserRepository()

    await users.save(
        BetaUserState(
            user_id="david",
            email="david@example.com",
            email_verified=True,
            beta_approved=True,
            active_world_id=None,
        )
    )

    service = create_service(users)

    with pytest.raises(
        ValueError,
        match="World not found",
    ):
        await service.assign_world(
            user_id="david",
            world_id="invented_world",
        )


@pytest.mark.asyncio
async def test_assign_world_does_not_persist_unknown_world():
    users = InMemoryBetaUserRepository()

    await users.save(
        BetaUserState(
            user_id="david",
            email="david@example.com",
            email_verified=True,
            beta_approved=True,
            active_world_id="french_world",
        )
    )

    service = create_service(users)

    with pytest.raises(
        ValueError,
        match="World not found",
    ):
        await service.assign_world(
            user_id="david",
            world_id="invented_world",
        )

    persisted = await users.get("david")

    assert persisted is not None
    assert persisted.active_world_id == "french_world"