from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.infrastructure.persistence.postgresql_user_policy_profile_repository import (
    PostgreSQLUserPolicyProfileRepository,
)


class FakeSession:
    def __init__(self, existing_record=None):
        self.existing_record = existing_record
        self.added_record = None
        self.committed = False
        self.refreshed_record = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def scalar(self, statement):
        return self.existing_record

    def add(self, record):
        self.added_record = record

    def commit(self):
        self.committed = True

    def refresh(self, record):
        self.refreshed_record = record


def test_repository_rejects_missing_session_factory():
    with pytest.raises(ValueError, match="session_factory"):
        PostgreSQLUserPolicyProfileRepository(None)


def test_repository_rejects_missing_user_id():
    repository = PostgreSQLUserPolicyProfileRepository.__new__(
        PostgreSQLUserPolicyProfileRepository
    )
    repository._session_factory = lambda: None

    with pytest.raises(ValueError, match="user_id"):
        repository.get_by_user_id(user_id=None)


def test_repository_rejects_empty_policy_classification():
    repository = PostgreSQLUserPolicyProfileRepository.__new__(
        PostgreSQLUserPolicyProfileRepository
    )
    repository._session_factory = lambda: None

    with pytest.raises(
        ValueError,
        match="policy_classification",
    ):
        repository.upsert(
            user_id=uuid4(),
            policy_classification="",
            guardian_required=True,
            policy_version="P5B.6.2B.2",
            policy_effective_at=datetime.now(timezone.utc),
        )


def test_repository_rejects_empty_policy_version():
    repository = PostgreSQLUserPolicyProfileRepository.__new__(
        PostgreSQLUserPolicyProfileRepository
    )
    repository._session_factory = lambda: None

    with pytest.raises(ValueError, match="policy_version"):
        repository.upsert(
            user_id=uuid4(),
            policy_classification="minor",
            guardian_required=True,
            policy_version="",
            policy_effective_at=datetime.now(timezone.utc),
        )


def test_repository_rejects_missing_effective_time():
    repository = PostgreSQLUserPolicyProfileRepository.__new__(
        PostgreSQLUserPolicyProfileRepository
    )
    repository._session_factory = lambda: None

    with pytest.raises(ValueError, match="policy_effective_at"):
        repository.upsert(
            user_id=uuid4(),
            policy_classification="minor",
            guardian_required=True,
            policy_version="P5B.6.2B.2",
            policy_effective_at=None,
        )


def test_repository_get_by_user_id_returns_existing_record():
    user_id = uuid4()
    existing_record = object()
    session = FakeSession(existing_record=existing_record)

    repository = PostgreSQLUserPolicyProfileRepository.__new__(
        PostgreSQLUserPolicyProfileRepository
    )
    repository._session_factory = lambda: session

    result = repository.get_by_user_id(user_id=user_id)

    assert result is existing_record


def test_repository_upsert_creates_new_record():
    user_id = uuid4()
    effective_at = datetime.now(timezone.utc)
    session = FakeSession()

    repository = PostgreSQLUserPolicyProfileRepository.__new__(
        PostgreSQLUserPolicyProfileRepository
    )
    repository._session_factory = lambda: session

    result = repository.upsert(
        user_id=user_id,
        policy_classification="minor",
        guardian_required=True,
        policy_version="P5B.6.2B.2",
        policy_effective_at=effective_at,
        jurisdiction="LU",
    )

    assert result is session.added_record
    assert result.user_id == user_id
    assert result.policy_classification == "minor"
    assert result.guardian_required is True
    assert result.policy_version == "P5B.6.2B.2"
    assert result.jurisdiction == "LU"
    assert result.policy_effective_at == effective_at
    assert session.committed is True
    assert session.refreshed_record is result


def test_repository_upsert_updates_existing_record():
    user_id = uuid4()
    original_effective_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    new_effective_at = datetime(2026, 9, 22, tzinfo=timezone.utc)

    from app.infrastructure.persistence.user_policy_profile_models import (
        UserPolicyProfileRecord,
    )

    existing_record = UserPolicyProfileRecord(
        user_id=user_id,
        policy_classification="adult",
        guardian_required=False,
        policy_version="P5B.6.2B.1",
        policy_effective_at=original_effective_at,
        jurisdiction="ES",
    )

    session = FakeSession(existing_record=existing_record)

    repository = PostgreSQLUserPolicyProfileRepository.__new__(
        PostgreSQLUserPolicyProfileRepository
    )
    repository._session_factory = lambda: session

    result = repository.upsert(
        user_id=user_id,
        policy_classification="minor",
        guardian_required=True,
        policy_version="P5B.6.2B.2",
        policy_effective_at=new_effective_at,
        jurisdiction="LU",
    )

    assert result is existing_record
    assert result.policy_classification == "minor"
    assert result.guardian_required is True
    assert result.policy_version == "P5B.6.2B.2"
    assert result.policy_effective_at == new_effective_at
    assert result.jurisdiction == "LU"
    assert session.committed is True
    assert session.refreshed_record is result
    assert session.added_record is None