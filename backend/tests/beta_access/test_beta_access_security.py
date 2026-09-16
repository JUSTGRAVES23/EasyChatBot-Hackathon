from __future__ import annotations

import pytest

from app.application.beta_access.beta_access_service import BetaAccessService
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
    from pathlib import Path

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


@pytest.mark.asyncio
async def test_telegram_identity_cannot_be_owned_by_two_users():
    users = InMemoryBetaUserRepository()
    tokens = InMemoryBetaTokenRepository()
    bindings = InMemoryTelegramBindingRepository()

    service = BetaAccessService(
        user_repository=users,
        token_repository=tokens,
        binding_repository=bindings,
        world_resolver=create_world_resolver(),
    )

    for user_id in ("a", "b"):
        await users.save(
            BetaUserState(
                user_id=user_id,
                email=f"{user_id}@example.com",
                email_verified=True,
                beta_approved=True,
                active_world_id="world-fr",
            )
        )

    first = await service.create_connection_token("a")

    await service.validate_and_bind(
        token=first.token,
        telegram_id=111,
        chat_id=111,
    )

    second = await service.create_connection_token("b")

    with pytest.raises(ValueError, match="already connected"):
        await service.validate_and_bind(
            token=second.token,
            telegram_id=111,
            chat_id=111,
        )