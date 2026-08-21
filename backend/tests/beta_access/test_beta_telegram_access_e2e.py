from datetime import datetime, timedelta, timezone

import pytest

from app.application.beta_access.beta_access_service import BetaAccessService
from app.application.beta_access.models import BetaUserState
from app.application.beta_access.email_workflow import BetaTelegramInvitationService
from app.infrastructure.email.in_memory_beta_email_sender import InMemoryBetaEmailSender
from app.interfaces.telegram.beta_start_handler import BetaTelegramStartHandler
from app.interfaces.telegram.private_chat_gate import BetaPrivateChatGate


class Users:
    def __init__(self):
        self.items = {}
    async def get(self, user_id):
        return self.items.get(user_id)
    async def get_by_telegram_id(self, telegram_id):
        return next((u for u in self.items.values() if u.telegram_id == telegram_id), None)
    async def save(self, user):
        self.items[user.user_id] = user
        return user


class Tokens:
    def __init__(self):
        self.items = {}
    async def get_by_hash(self, token_hash):
        return next((t for t in self.items.values() if t.token_hash == token_hash), None)
    async def save(self, token):
        self.items[token.token_id] = token
        return token
    async def mark_used(self, token):
        self.items[token.token_id] = token
        return token


class Bindings:
    def __init__(self):
        self.items = {}
    async def get_by_telegram_user_id(self, telegram_user_id):
        return next((b for b in self.items.values() if b.telegram_user_id == telegram_user_id), None)
    async def get_by_user_id(self, user_id):
        return next((b for b in self.items.values() if b.user_id == user_id), None)
    async def save(self, binding):
        self.items[binding.binding_id] = binding
        return binding


@pytest.mark.asyncio
async def test_complete_beta_telegram_vertical_slice():
    users = Users()
    tokens = Tokens()
    bindings = Bindings()

    users.items["u1"] = BetaUserState(
        user_id="u1",
        email="learner@example.com",
        email_verified=True,
        beta_approved=True,
        active_world_id="fr_world",
    )

    access = BetaAccessService(
        user_repository=users,
        token_repository=tokens,
        binding_repository=bindings,
    )

    email = InMemoryBetaEmailSender()
    invitation = BetaTelegramInvitationService(
        beta_access_service=access,
        email_sender=email,
        telegram_bot_username="EasyChatBotAcademyBot",
    )

    deep_link = await invitation.send_invitation(user_id="u1")
    raw_token = deep_link.split("?start=", 1)[1]

    replies = []

    async def reply(message, user):
        replies.append(message)

    handler = BetaTelegramStartHandler(
        beta_access_service=access,
        reply=reply,
    )

    await handler.handle(
        token=raw_token,
        telegram_user_id=12345,
        chat_id=12345,
        chat_type="private",
    )

    assert email.messages[0]["email"] == "learner@example.com"
    assert "start=" in email.messages[0]["classroom_url"]
    assert replies
    assert "connected" in replies[0].lower()

    gate = BetaPrivateChatGate(beta_access_service=access)
    assert await gate.authorize(telegram_user_id=12345) is True


@pytest.mark.asyncio
async def test_token_is_single_use():
    users = Users()
    tokens = Tokens()
    bindings = Bindings()

    users.items["u1"] = BetaUserState(
        user_id="u1",
        email="learner@example.com",
        email_verified=True,
        beta_approved=True,
        active_world_id="fr_world",
    )

    access = BetaAccessService(
        user_repository=users,
        token_repository=tokens,
        binding_repository=bindings,
    )

    raw_token, _ = await access.create_connection_token("u1")

    await access.validate_and_bind(
        token=raw_token,
        telegram_id=100,
        chat_id=100,
    )

    with pytest.raises(ValueError, match="already used"):
        await access.validate_and_bind(
            token=raw_token,
            telegram_id=101,
            chat_id=101,
        )


@pytest.mark.asyncio
async def test_group_chat_cannot_bind():
    users = Users()
    tokens = Tokens()
    bindings = Bindings()

    users.items["u1"] = BetaUserState(
        user_id="u1",
        email="learner@example.com",
        email_verified=True,
        beta_approved=True,
        active_world_id="fr_world",
    )

    access = BetaAccessService(
        user_repository=users,
        token_repository=tokens,
        binding_repository=bindings,
    )

    raw_token, _ = await access.create_connection_token("u1")

    replies = []

    async def reply(message, user):
        replies.append(message)

    handler = BetaTelegramStartHandler(
        beta_access_service=access,
        reply=reply,
    )

    await handler.handle(
        token=raw_token,
        telegram_user_id=1,
        chat_id=-100,
        chat_type="group",
    )

    assert "private" in replies[0].lower()
