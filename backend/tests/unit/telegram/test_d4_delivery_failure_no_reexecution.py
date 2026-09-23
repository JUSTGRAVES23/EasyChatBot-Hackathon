from __future__ import annotations

from app.application.failures.provider_failure import ProviderFailure
from app.interfaces.telegram.beta_telegram_adapter import BetaTelegramAdapter


class FakeMessage:
    def __init__(
        self,
        text: str = "Hello EasyWorld",
    ) -> None:
        self.text = text
        self.photo_calls: list[dict] = []
        self.text_calls: list[dict] = []

    async def reply_photo(
        self,
        **kwargs,
    ):
        self.photo_calls.append(kwargs)

        raise RuntimeError(
            "simulated Telegram delivery failure"
        )

    async def reply_text(
        self,
        text,
        **kwargs,
    ):
        self.text_calls.append(
            {
                "text": text,
                **kwargs,
            }
        )


class FakeUser:
    id = 123456789


class FakeChat:
    type = "private"


class FakeUpdate:
    def __init__(
        self,
        message: FakeMessage,
    ) -> None:
        self.effective_user = FakeUser()
        self.effective_chat = FakeChat()
        self.effective_message = message


class FakeStartHandler:
    async def handle(
        self,
        *args,
        **kwargs,
    ):
        return None


class FakePrivateChatGate:
    async def authorize(
        self,
        *,
        telegram_user_id,
        chat_type,
    ):
        return True


class FakeBoundary:
    def __init__(self) -> None:
        self.calls = 0

    async def handle_message(
        self,
        *,
        telegram_user_id,
        message,
    ):
        self.calls += 1

        raise ProviderFailure(
            code="PROVIDER_TEMPORARILY_UNAVAILABLE",
            message="Provider unavailable.",
            provider_id="ollama",
            provider_request_id="test-provider-request-002",
        )


class FakeWorldStartRouter:
    def resolve(
        self,
        token,
    ):
        return None


async def test_delivery_failure_does_not_reexecute_ai():
    message = FakeMessage()

    boundary = FakeBoundary()

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=FakePrivateChatGate(),
        conversation_boundary=boundary,
        world_start_router=FakeWorldStartRouter(),
        failure_information_url=(
            "https://example.com/provider-unavailable"
        ),
    )

    update = FakeUpdate(
        message,
    )

    result = await adapter.handle_message(
        update,
    )

    # Provider failure is contained.
    assert result is None

    # ---------------------------------------------------------
    # CRITICAL INVARIANT:
    #
    # The application/AI path executes exactly once.
    # Telegram delivery failure MUST NOT re-execute it.
    # ---------------------------------------------------------

    assert boundary.calls == 1

    # The adapter attempted exactly one branded response.
    assert len(message.photo_calls) == 1

    # There must be no second application execution.
    assert boundary.calls == 1


def test_d4_6_marker():
    print(
        "D4.6 TEST MODULE: LOADED"
    )
