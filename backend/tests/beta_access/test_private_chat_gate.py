from app.interfaces.telegram.beta_telegram_private_chat_gate import (
    BetaTelegramPrivateChatGate,
)


class StubAccess:
    def __init__(self, active: bool):
        self.active = active

    def is_active(self, *, user_id: str) -> bool:
        return self.active


def test_private_chat_gate_rejects_group():
    gate = BetaTelegramPrivateChatGate(
        beta_access_service=StubAccess(True)
    )
    assert gate.authorize(user_id="u1", chat_type="group") is False


def test_private_chat_gate_accepts_active_private_user():
    gate = BetaTelegramPrivateChatGate(
        beta_access_service=StubAccess(True)
    )
    assert gate.authorize(user_id="u1", chat_type="private") is True


def test_private_chat_gate_rejects_inactive_private_user():
    gate = BetaTelegramPrivateChatGate(
        beta_access_service=StubAccess(False)
    )
    assert gate.authorize(user_id="u1", chat_type="private") is False
