from __future__ import annotations

from pathlib import Path

from telegram import InlineKeyboardMarkup

from app.application.failures.provider_failure import ProviderFailure
from app.interfaces.telegram.beta_telegram_adapter import BetaTelegramAdapter


TEST_INFORMATION_URL = (
    "https://example.com/provider-unavailable"
)


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
        assert telegram_user_id == 123456789
        assert chat_type == "private"

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

        assert telegram_user_id == 123456789
        assert message == "Hello EasyWorld"

        raise ProviderFailure(
            code="PROVIDER_TEMPORARILY_UNAVAILABLE",
            message="Provider unavailable.",
            provider_id="ollama",
            provider_request_id="test-provider-request-001",
        )


class FakeWorldStartRouter:
    def resolve(
        self,
        token,
    ):
        return None


async def test_provider_failure_telegram_response():
    message = FakeMessage(
        text="Hello EasyWorld",
    )

    boundary = FakeBoundary()

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=FakePrivateChatGate(),
        conversation_boundary=boundary,
        world_start_router=FakeWorldStartRouter(),
        failure_information_url=TEST_INFORMATION_URL,
    )

    update = FakeUpdate(
        message,
    )

    result = await adapter.handle_message(
        update,
    )

    # ---------------------------------------------------------
    # Provider failure must be handled by the adapter.
    # ---------------------------------------------------------

    assert result is None

    # ---------------------------------------------------------
    # The application/AI path executes exactly once.
    # ---------------------------------------------------------

    assert boundary.calls == 1

    # ---------------------------------------------------------
    # Exactly one branded Telegram response.
    # ---------------------------------------------------------

    assert len(message.photo_calls) == 1

    # No second/generic Telegram response.
    assert len(message.text_calls) == 0

    photo_call = message.photo_calls[0]

    assert "photo" in photo_call
    assert "caption" in photo_call
    assert "reply_markup" in photo_call

    # ---------------------------------------------------------
    # Transparent user-facing message.
    # ---------------------------------------------------------

    caption = photo_call["caption"]

    assert (
        "temporarily unavailable"
        in caption.lower()
    )

    assert (
        "working to restore it"
        in caption.lower()
    )

    assert (
        "try again shortly"
        in caption.lower()
    )

    # ---------------------------------------------------------
    # Canonical branded asset.
    # ---------------------------------------------------------

    photo = photo_call["photo"]

    assert photo is not None

    if hasattr(photo, "name"):
        assert (
            Path(photo.name).name
            == "Provider Temporarily Unavailable.png"
        )

    # ---------------------------------------------------------
    # More Information CTA.
    # ---------------------------------------------------------

    markup = photo_call["reply_markup"]

    assert isinstance(
        markup,
        InlineKeyboardMarkup,
    )

    buttons = [
        button
        for row in markup.inline_keyboard
        for button in row
    ]

    assert any(
        button.text == "More information"
        and button.url == TEST_INFORMATION_URL
        for button in buttons
    )


def test_d4_marker():
    print(
        "D4.4 TEST MODULE: LOADED"
    )