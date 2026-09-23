
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.telegram.telegram_bot_runtime import (
    TelegramBotRuntime,
)


@pytest.mark.asyncio
async def test_duplicate_private_update_does_not_reach_adapter() -> None:
    adapter = MagicMock()
    adapter.handle_message = AsyncMock()

    idempotency = MagicMock()
    idempotency.claim.return_value = False

    runtime = TelegramBotRuntime(
        adapter=adapter,
        telegram_update_idempotency=idempotency,
    )

    update = MagicMock()
    update.update_id = 847392

    context = MagicMock()

    await runtime._handle_private_message(
        update,
        context,
    )

    idempotency.claim.assert_called_once_with(847392)
    adapter.handle_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_first_private_update_reaches_adapter() -> None:
    adapter = MagicMock()
    adapter.handle_message = AsyncMock()

    idempotency = MagicMock()
    idempotency.claim.return_value = True

    runtime = TelegramBotRuntime(
        adapter=adapter,
        telegram_update_idempotency=idempotency,
    )

    update = MagicMock()
    update.update_id = 847393

    context = MagicMock()

    await runtime._handle_private_message(
        update,
        context,
    )

    idempotency.claim.assert_called_once_with(847393)
    adapter.handle_message.assert_awaited_once_with(
        update,
        context,
    )
