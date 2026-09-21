from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.domain.learning.learner_world_access import (
    ACTIVE,
    BETA,
    REVOKED,
    LearnerWorldAccess,
)


def test_grant_creates_active_access() -> None:
    user_id = uuid4()
    world_id = uuid4()
    now = datetime.now(timezone.utc)

    access = LearnerWorldAccess.grant(
        user_id=user_id,
        world_id=world_id,
        access_source=BETA,
        now=now,
    )

    assert access.user_id == user_id
    assert access.world_id == world_id
    assert access.status == ACTIVE
    assert access.access_source == BETA
    assert access.created_at == now
    assert access.updated_at == now


def test_revoke_is_immutable_and_updates_timestamp() -> None:
    access = LearnerWorldAccess.grant(
        user_id=uuid4(),
        world_id=uuid4(),
        access_source=BETA,
    )

    revoked = access.revoke()

    assert access.status == ACTIVE
    assert revoked.status == REVOKED
    assert revoked.access_id == access.access_id
    assert revoked.updated_at >= access.updated_at


def test_invalid_access_source_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported access source"):
        LearnerWorldAccess.grant(
            user_id=uuid4(),
            world_id=uuid4(),
            access_source="unknown",
        )
