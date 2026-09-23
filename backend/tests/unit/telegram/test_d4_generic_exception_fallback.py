from __future__ import annotations

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
    def __init__(self) -> None:
        self.calls = 0

    async def handle_message(
        self,
        *,
        telegram_user_id,
        message,
    ):
        self.calls += 1

        raise RuntimeError(
            "simulated unexpected application failure"
        )


class FakeWorldStartRouter:
    def resolve(
        self,
        token,
    ):
        return None


async def test_unexpected_exception_preserves_generic_fallback():
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

    # Unexpected exceptions are contained.
    assert result is None

    # Application path executed exactly once.
    assert boundary.calls == 1

    # Existing generic fallback is text-only.
    assert len(message.text_calls) == 1

    assert len(message.photo_calls) == 0

    response = message.text_calls[0]["text"]

    assert (
        response
        == (
            "Sorry, I could not process "
            "your classroom message. "
            "Please try again."
        )
    )

    # No provider-specific CTA leaked into generic failure.
    assert "More information" not in response
    assert "temporarily unavailable" not in response.lower()


def test_d4_5_marker():
    print(
        "D4.5 TEST MODULE: LOADED"
    )