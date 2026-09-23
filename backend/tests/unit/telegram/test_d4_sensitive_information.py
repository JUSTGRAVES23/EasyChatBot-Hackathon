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
    async def handle_message(
        self,
        *,
        telegram_user_id,
        message,
    ):
        raise ProviderFailure(
            code="PROVIDER_TEMPORARILY_UNAVAILABLE",
            message=(
                "INTERNAL_PROVIDER_ERROR: "
                "connection refused at 127.0.0.1:11434; "
                "provider_request_id=SECRET-REQUEST-123"
            ),
            provider_id="SECRET-PROVIDER",
            provider_request_id="SECRET-REQUEST-123",
        )


class FakeWorldStartRouter:
    def resolve(
        self,
        token,
    ):
        return None


async def test_provider_failure_does_not_leak_sensitive_details():
    message = FakeMessage()

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=FakePrivateChatGate(),
        conversation_boundary=FakeBoundary(),
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

    assert result is None

    assert len(message.photo_calls) == 1

    caption = message.photo_calls[0]["caption"]

    # ---------------------------------------------------------
    # Safe user-facing information MUST remain present.
    # ---------------------------------------------------------

    assert (
        "temporarily unavailable"
        in caption.lower()
    )

    assert (
        "try again shortly"
        in caption.lower()
    )

    # ---------------------------------------------------------
    # Internal provider information MUST NOT leak.
    # ---------------------------------------------------------

    forbidden_values = [
        "INTERNAL_PROVIDER_ERROR",
        "SECRET-REQUEST-123",
        "SECRET-PROVIDER",
        "127.0.0.1:11434",
        "connection refused",
        "Provider unavailable.",
    ]

    for forbidden in forbidden_values:
        assert forbidden not in caption


def test_d4_7_marker():
    print(
        "D4.7 TEST MODULE: LOADED"
    )
