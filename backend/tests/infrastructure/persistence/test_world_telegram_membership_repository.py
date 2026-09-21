"""Persistence contract tests for World Telegram membership."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.domain.world_telegram import (
    TelegramMembershipStatus,
    WorldTelegramMembership,
)


def test_membership_domain_contract():
    now = datetime.now(timezone.utc)
    membership = WorldTelegramMembership(
        id=uuid4(),
        destination_id=uuid4(),
        user_id=uuid4(),
        status=TelegramMembershipStatus.ACTIVE,
        joined_at=now,
        left_at=None,
        created_at=now,
        updated_at=now,
    )

    assert membership.status is TelegramMembershipStatus.ACTIVE
    assert membership.left_at is None
    assert isinstance(membership.user_id, UUID)
