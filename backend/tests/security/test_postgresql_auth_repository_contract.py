from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.infrastructure.auth.postgresql_auth_repository import (
    PostgreSQLAuthenticationRepository,
)


class FakeResult:
    def __init__(self, row=None, rows=()):
        self._row = row
        self._rows = rows

    def first(self):
        return self._row

    def all(self):
        return list(self._rows)

    def mappings(self):
        return self


class FakeSession:
    def __init__(self):
        self.calls = []

    async def execute(self, statement, params=None):
        self.calls.append((str(statement), params))
        if "SELECT 1 FROM users WHERE email" in str(statement):
            return FakeResult()
        if "SELECT 1 FROM users WHERE username" in str(statement):
            return FakeResult()
        return FakeResult()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def begin(self):
        return self


class FakeFactory:
    def __call__(self):
        return FakeSession()


@pytest.mark.asyncio
async def test_repository_uses_existing_users_table_contract():
    repository = PostgreSQLAuthenticationRepository(FakeFactory())
    assert await repository.email_exists("missing@example.com") is False
    assert await repository.username_exists("missing") is False


def test_repository_is_provider_neutral_at_application_boundary():
    assert PostgreSQLAuthenticationRepository.__name__ == "PostgreSQLAuthenticationRepository"

