from __future__ import annotations

import pytest

from app.application.internal_data.beta_user_read_service import (
    BetaUserReadService,
)


class FakeUser:
    user_id = "user-123"
    email = "test@example.com"
    email_verified = True
    beta_approved = True
    telegram_id = 123456789
    active_world_id = "french"


class FakeRepository:
    def __init__(self):
        self.get_calls = []
        self.telegram_calls = []

    async def get(self, user_id):
        self.get_calls.append(user_id)
        return FakeUser()

    async def get_by_telegram_id(self, telegram_id):
        self.telegram_calls.append(telegram_id)
        return FakeUser()


@pytest.mark.asyncio
async def test_get_beta_user_returns_safe_dto():
    repository = FakeRepository()
    service = BetaUserReadService(repository)

    result = await service.get_beta_user("user-123")

    assert result == {
        "user_id": "user-123",
        "email": "test@example.com",
        "email_verified": True,
        "beta_approved": True,
        "telegram_id": 123456789,
        "active_world_id": "french",
    }

    assert repository.get_calls == ["user-123"]


@pytest.mark.asyncio
async def test_get_beta_user_by_telegram_id_returns_safe_dto():
    repository = FakeRepository()
    service = BetaUserReadService(repository)

    result = await service.get_beta_user_by_telegram_id(
        123456789
    )

    assert result["user_id"] == "user-123"
    assert repository.telegram_calls == [123456789]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "value",
    ["", "   ", None, 123, "x" * 129],
)
async def test_invalid_user_id_is_rejected(value):
    repository = FakeRepository()
    service = BetaUserReadService(repository)

    with pytest.raises(ValueError):
        await service.get_beta_user(value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "value",
    [0, -1, None, "123", True, False],
)
async def test_invalid_telegram_id_is_rejected(value):
    repository = FakeRepository()
    service = BetaUserReadService(repository)

    with pytest.raises(ValueError):
        await service.get_beta_user_by_telegram_id(value)


@pytest.mark.asyncio
async def test_missing_user_returns_none():
    class EmptyRepository(FakeRepository):
        async def get(self, user_id):
            return None

    service = BetaUserReadService(
        EmptyRepository()
    )

    result = await service.get_beta_user("user-123")

    assert result is None

def test_read_repository_protocol_exposes_only_reads():
    from app.application.internal_data.beta_user_read_repository import (
        BetaUserReadRepository,
    )

    assert hasattr(
        BetaUserReadRepository,
        "get",
    )

    assert hasattr(
        BetaUserReadRepository,
        "get_by_telegram_id",
    )

    assert not hasattr(
        BetaUserReadRepository,
        "save",
    )

