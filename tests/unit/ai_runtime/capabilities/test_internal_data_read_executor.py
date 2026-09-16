from __future__ import annotations

import pytest

from src.ai_runtime.capabilities.internal_data_read_executor import (
    InternalDataReadExecutor,
)
from src.ai_runtime.capabilities.models import (
    CapabilityRequest,
    CapabilityType,
)


class FakeReadService:
    async def get_beta_user(self, user_id):
        return {
            "user_id": user_id,
            "email": "test@example.com",
        }

    async def get_beta_user_by_telegram_id(
        self,
        telegram_id,
    ):
        return {
            "user_id": "user-123",
            "telegram_id": telegram_id,
        }


def request(payload):
    return CapabilityRequest(
        capability=CapabilityType.INTERNAL_DATA_READ,
        request_id="req-123",
        payload=payload,
        requested_by="test",
    )


@pytest.mark.asyncio
async def test_get_beta_user():
    executor = InternalDataReadExecutor(
        FakeReadService()
    )

    result = await executor.execute(
        request(
            {
                "operation": "get_beta_user",
                "user_id": "user-123",
            }
        )
    )

    assert result.succeeded
    assert result.output["found"] is True
    assert result.output["user"]["user_id"] == "user-123"


@pytest.mark.asyncio
async def test_get_beta_user_by_telegram_id():
    executor = InternalDataReadExecutor(
        FakeReadService()
    )

    result = await executor.execute(
        request(
            {
                "operation": (
                    "get_beta_user_by_telegram_id"
                ),
                "telegram_id": 123456789,
            }
        )
    )

    assert result.succeeded
    assert (
        result.output["user"]["telegram_id"]
        == 123456789
    )


@pytest.mark.asyncio
async def test_unknown_operation_rejected():
    executor = InternalDataReadExecutor(
        FakeReadService()
    )

    with pytest.raises(ValueError):
        await executor.execute(
            request(
                {
                    "operation": "execute_sql",
                    "user_id": "user-123",
                }
            )
        )


@pytest.mark.asyncio
async def test_both_identifiers_rejected():
    executor = InternalDataReadExecutor(
        FakeReadService()
    )

    with pytest.raises(ValueError):
        await executor.execute(
            request(
                {
                    "operation": "get_beta_user",
                    "user_id": "user-123",
                    "telegram_id": 123456789,
                }
            )
        )


@pytest.mark.asyncio
async def test_missing_identifier_rejected():
    executor = InternalDataReadExecutor(
        FakeReadService()
    )

    with pytest.raises(ValueError):
        await executor.execute(
            request(
                {
                    "operation": "get_beta_user",
                }
            )
        )


@pytest.mark.asyncio
async def test_wrong_capability_rejected():
    executor = InternalDataReadExecutor(
        FakeReadService()
    )

    wrong_request = CapabilityRequest(
        capability=CapabilityType.EVALUATION,
        request_id="req-123",
        payload={
            "operation": "get_beta_user",
            "user_id": "user-123",
        },
        requested_by="test",
    )

    with pytest.raises(ValueError):
        await executor.execute(
            wrong_request
        )

