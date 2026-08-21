import pytest

from app.application.beta_access.beta_access_service import BetaAccessService
from app.application.beta_access.models import BetaUserState
from app.infrastructure.persistence.in_memory_beta_access_repository import (
    InMemoryBetaTokenRepository,
    InMemoryBetaUserRepository,
    InMemoryTelegramBindingRepository,
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
