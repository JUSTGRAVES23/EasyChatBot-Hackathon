from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)


@dataclass(frozen=True)
class FakeConversationContext:
    world_id: str = "world-fr"
    character: str = "Alix"
    level: str = "B1"


class FakeBetaAccessService:
    """Deterministic Beta authorization/context test double."""

    def __init__(self, *, approved: bool = True) -> None:
        self.approved = approved
        self.calls: list[int] = []

    async def get_conversation_context(
        self,
        telegram_user_id: int,
    ) -> FakeConversationContext:
        self.calls.append(telegram_user_id)

        if not self.approved:
            raise PermissionError(
                "Telegram user is not approved."
            )

        return FakeConversationContext()


class FakeConversationService:
    """Deterministic downstream conversation-service double."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def handle_telegram_message(
        self,
        *,
        telegram_user_id: int,
        message: str,
    ) -> str:
        self.calls.append(
            {
                "telegram_user_id": telegram_user_id,
                "message": message,
            }
        )
        return "Bonjour !"


@dataclass(frozen=True)
class TelegramClassroomPolicy:
    """Configuration-driven WS-14 classroom policy."""

    max_message_length: int = 4096
    max_messages_per_user: int = 3
    enabled: bool = True


class TelegramClassroomPolicyValidator:
    """Validates classroom policy before it is used."""

    @staticmethod
    def validate(
        policy: TelegramClassroomPolicy,
    ) -> None:
        if not isinstance(policy, TelegramClassroomPolicy):
            raise TypeError(
                "Telegram classroom policy must be a "
                "TelegramClassroomPolicy."
            )

        if not isinstance(policy.max_message_length, int):
            raise TypeError(
                "max_message_length must be an integer."
            )

        if policy.max_message_length <= 0:
            raise ValueError(
                "max_message_length must be greater than zero."
            )

        if not isinstance(policy.max_messages_per_user, int):
            raise TypeError(
                "max_messages_per_user must be an integer."
            )

        if policy.max_messages_per_user <= 0:
            raise ValueError(
                "max_messages_per_user must be greater than zero."
            )

        if not isinstance(policy.enabled, bool):
            raise TypeError(
                "enabled must be a boolean."
            )


class FakePolicyEnforcer:
    """
    Deterministic policy enforcer.

    State is explicitly scoped by Telegram identity.
    """

    def __init__(
        self,
        *,
        policy: TelegramClassroomPolicy,
    ) -> None:
        TelegramClassroomPolicyValidator.validate(policy)

        self.policy = policy
        self.calls: list[int] = []
        self._counts: dict[int, int] = {}

    async def allow(
        self,
        *,
        telegram_user_id: int,
    ) -> bool:
        self.calls.append(telegram_user_id)

        if not self.policy.enabled:
            return False

        count = self._counts.get(
            telegram_user_id,
            0,
        )

        if count >= self.policy.max_messages_per_user:
            return False

        self._counts[telegram_user_id] = count + 1
        return True


class PolicyControlledBoundary:
    """
    Minimal WS-14 integration composition.

    Policy validation and enforcement are deliberately kept outside
    the Telegram transport adapter and conversation service.
    """

    POLICY_DISABLED_RESPONSE = (
        "Sorry, the classroom is temporarily unavailable."
    )

    POLICY_LIMIT_RESPONSE = (
        "Sorry, you have reached the classroom message limit. "
        "Please try again later."
    )

    def __init__(
        self,
        *,
        conversation_service: FakeConversationService,
        beta_access_service: FakeBetaAccessService,
        policy: TelegramClassroomPolicy,
    ) -> None:
        TelegramClassroomPolicyValidator.validate(policy)

        self.policy = policy
        self._conversation_service = conversation_service
        self._beta_access_service = beta_access_service
        self._policy_enforcer = FakePolicyEnforcer(
            policy=policy,
        )

        self._conversation_boundary = BetaTelegramConversationBoundary(
            conversation_service=conversation_service,
            beta_access_service=beta_access_service,
        )

    async def handle_message(
        self,
        *,
        telegram_user_id: int,
        message: str,
    ) -> str:
        # Reuse the established WS-10 input validation contract before
        # consuming any configured classroom allowance.
        BetaTelegramConversationBoundary._validate_telegram_user_id(
            telegram_user_id,
        )

        clean_message = (
            BetaTelegramConversationBoundary._validate_message(
                message,
            )
        )

        if not self.policy.enabled:
            return self.POLICY_DISABLED_RESPONSE

        if len(clean_message) > self.policy.max_message_length:
            raise ValueError(
                "Telegram message is too long for the configured "
                "classroom policy."
            )

        if not await self._policy_enforcer.allow(
            telegram_user_id=telegram_user_id,
        ):
            return self.POLICY_LIMIT_RESPONSE

        return await self._conversation_boundary.handle_message(
            telegram_user_id=telegram_user_id,
            message=clean_message,
        )


def make_boundary(
    *,
    approved: bool = True,
    policy: TelegramClassroomPolicy | None = None,
):
    if policy is None:
        policy = TelegramClassroomPolicy()

    access = FakeBetaAccessService(
        approved=approved,
    )
    conversation_service = FakeConversationService()

    boundary = PolicyControlledBoundary(
        conversation_service=conversation_service,
        beta_access_service=access,
        policy=policy,
    )

    return (
        boundary,
        access,
        conversation_service,
    )


def test_ws14_default_policy_is_valid():
    policy = TelegramClassroomPolicy()

    TelegramClassroomPolicyValidator.validate(policy)

    assert policy.enabled is True
    assert policy.max_message_length == 4096
    assert policy.max_messages_per_user == 3


@pytest.mark.parametrize(
    "policy",
    [
        TelegramClassroomPolicy(
            max_message_length=0,
        ),
        TelegramClassroomPolicy(
            max_message_length=-1,
        ),
        TelegramClassroomPolicy(
            max_messages_per_user=0,
        ),
        TelegramClassroomPolicy(
            max_messages_per_user=-1,
        ),
    ],
)
def test_ws14_invalid_zero_or_negative_policy_is_rejected(
    policy: TelegramClassroomPolicy,
):
    with pytest.raises(ValueError):
        TelegramClassroomPolicyValidator.validate(policy)


def test_ws14_invalid_policy_types_are_rejected():
    with pytest.raises(TypeError):
        TelegramClassroomPolicyValidator.validate(
            TelegramClassroomPolicy(
                max_message_length="4096",  # type: ignore[arg-type]
            )
        )

    with pytest.raises(TypeError):
        TelegramClassroomPolicyValidator.validate(
            TelegramClassroomPolicy(
                max_messages_per_user="3",  # type: ignore[arg-type]
            )
        )

    with pytest.raises(TypeError):
        TelegramClassroomPolicyValidator.validate(
            TelegramClassroomPolicy(
                enabled="yes",  # type: ignore[arg-type]
            )
        )


@pytest.mark.asyncio
async def test_ws14_configured_message_limit_is_applied():
    policy = TelegramClassroomPolicy(
        max_message_length=10,
        max_messages_per_user=3,
    )

    boundary, access, conversation_service = make_boundary(
        policy=policy,
    )

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert response == "Bonjour !"

    assert access.calls == [12345]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_ws14_configured_message_limit_rejects_oversized_input():
    policy = TelegramClassroomPolicy(
        max_message_length=10,
        max_messages_per_user=3,
    )

    boundary, access, conversation_service = make_boundary(
        policy=policy,
    )

    with pytest.raises(
        ValueError,
        match="configured classroom policy",
    ):
        await boundary.handle_message(
            telegram_user_id=12345,
            message="A" * 11,
        )

    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws14_configured_per_user_message_limit_is_enforced():
    policy = TelegramClassroomPolicy(
        max_message_length=4096,
        max_messages_per_user=1,
    )

    boundary, access, conversation_service = make_boundary(
        policy=policy,
    )

    first = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    second = await boundary.handle_message(
        telegram_user_id=12345,
        message="Encore",
    )

    assert first == "Bonjour !"
    assert "message limit" in second.lower()

    assert access.calls == [12345]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_ws14_policy_limit_is_scoped_per_telegram_identity():
    policy = TelegramClassroomPolicy(
        max_messages_per_user=1,
    )

    boundary, access, conversation_service = make_boundary(
        policy=policy,
    )

    first = await boundary.handle_message(
        telegram_user_id=111,
        message="Bonjour",
    )

    blocked = await boundary.handle_message(
        telegram_user_id=111,
        message="Again",
    )

    second_user = await boundary.handle_message(
        telegram_user_id=222,
        message="Bonjour",
    )

    assert first == "Bonjour !"
    assert "message limit" in blocked.lower()
    assert second_user == "Bonjour !"

    assert access.calls == [
        111,
        222,
    ]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 111,
            "message": "Bonjour",
        },
        {
            "telegram_user_id": 222,
            "message": "Bonjour",
        },
    ]


@pytest.mark.asyncio
async def test_ws14_disabled_policy_fails_closed():
    policy = TelegramClassroomPolicy(
        enabled=False,
    )

    boundary, access, conversation_service = make_boundary(
        policy=policy,
    )

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert response
    assert "temporarily unavailable" in response.lower()

    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws14_unauthorized_user_does_not_reach_conversation_service():
    policy = TelegramClassroomPolicy(
        max_messages_per_user=3,
    )

    boundary, access, conversation_service = make_boundary(
        approved=False,
        policy=policy,
    )

    response = await boundary.handle_message(
        telegram_user_id=99999,
        message="Bonjour",
    )

    assert response
    assert "authorized" in response.lower()

    assert access.calls == [99999]
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws14_invalid_input_does_not_consume_policy_allowance():
    policy = TelegramClassroomPolicy(
        max_messages_per_user=1,
    )

    boundary, access, conversation_service = make_boundary(
        policy=policy,
    )

    with pytest.raises(
        ValueError,
        match="Telegram message cannot be empty",
    ):
        await boundary.handle_message(
            telegram_user_id=12345,
            message="   ",
        )

    # No authorization or conversation processing is permitted.
    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws14_policy_change_requires_no_application_code_change():
    restrictive_policy = TelegramClassroomPolicy(
        max_messages_per_user=1,
    )

    permissive_policy = TelegramClassroomPolicy(
        max_messages_per_user=2,
    )

    restrictive_boundary, _, restrictive_service = make_boundary(
        policy=restrictive_policy,
    )

    permissive_boundary, _, permissive_service = make_boundary(
        policy=permissive_policy,
    )

    assert await restrictive_boundary.handle_message(
        telegram_user_id=12345,
        message="One",
    ) == "Bonjour !"

    assert "message limit" in (
        await restrictive_boundary.handle_message(
            telegram_user_id=12345,
            message="Two",
        )
    ).lower()

    assert await permissive_boundary.handle_message(
        telegram_user_id=12345,
        message="One",
    ) == "Bonjour !"

    assert await permissive_boundary.handle_message(
        telegram_user_id=12345,
        message="Two",
    ) == "Bonjour !"

    assert restrictive_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "One",
        }
    ]

    assert permissive_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "One",
        },
        {
            "telegram_user_id": 12345,
            "message": "Two",
        },
    ]

