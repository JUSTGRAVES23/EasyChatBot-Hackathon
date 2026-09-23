
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.infrastructure.persistence.postgresql_telegram_update_idempotency_repository import (
    PostgreSQLTelegramUpdateIdempotencyRepository,
)


class _FakeResult:
    def __init__(self, rowcount: int) -> None:
        self.rowcount = rowcount


class _FakeSession:
    def __init__(self, rowcount: int) -> None:
        self.rowcount = rowcount
        self.executed_statement = None
        self.committed = False

    def execute(self, statement):
        self.executed_statement = statement
        return _FakeResult(self.rowcount)

    def commit(self) -> None:
        self.committed = True


def _build_repository(rowcount: int):
    session = _FakeSession(rowcount)

    session_factory = MagicMock()
    session_factory.return_value.__enter__.return_value = session

    repository = PostgreSQLTelegramUpdateIdempotencyRepository(
        session_factory=session_factory,
    )

    return repository, session, session_factory


def test_claim_returns_true_when_update_is_inserted() -> None:
    repository, session, session_factory = _build_repository(
        rowcount=1,
    )

    result = repository.claim(847392)

    assert result is True
    assert session.committed is True
    session_factory.assert_called_once()


def test_claim_returns_false_when_update_already_exists() -> None:
    repository, session, session_factory = _build_repository(
        rowcount=0,
    )

    result = repository.claim(847392)

    assert result is False
    assert session.committed is True
    session_factory.assert_called_once()


def test_claim_rejects_negative_update_id() -> None:
    repository, session, session_factory = _build_repository(
        rowcount=1,
    )

    with pytest.raises(
        ValueError,
        match="telegram_update_id must be non-negative",
    ):
        repository.claim(-1)

    session_factory.assert_not_called()
    assert session.committed is False

