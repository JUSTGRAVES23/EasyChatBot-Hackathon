from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.infrastructure.auth.postgresql_auth_repository import (
    PostgreSQLAuthenticationRepository,
)
from app.infrastructure.persistence.database import (
    create_async_database_engine,
    create_async_session_factory,
)


pytestmark = pytest.mark.integration


def _create_test_database():
    engine = create_async_database_engine()
    session_factory = create_async_session_factory(engine)
    return engine, session_factory


async def _create_test_user(
    session_factory,
    *,
    user_id,
    email: str,
    username: str,
) -> None:
    repository = PostgreSQLAuthenticationRepository(session_factory)

    await repository.create_user(
        user_id=user_id,
        email=email,
        username=username,
    )


async def _create_test_credential(
    session_factory,
    *,
    user_id,
    password_hash: str,
) -> None:
    repository = PostgreSQLAuthenticationRepository(session_factory)

    await repository.create_password_credential(
        user_id=user_id,
        password_hash=password_hash,
    )


async def _create_test_session(
    session_factory,
    *,
    user_id,
    session_id,
) -> None:
    repository = PostgreSQLAuthenticationRepository(session_factory)

    now = datetime.now(timezone.utc)

    await repository.create_session(
        session_id=session_id,
        user_id=user_id,
        created_at=now,
        expires_at=now + timedelta(hours=12),
        device_name="password-reset-integration-test",
        ip_address="127.0.0.1",
    )


async def _delete_test_data(
    session_factory,
    *,
    user_id,
) -> None:
    async with session_factory() as session:
        await session.execute(
            text(
                """
                DELETE FROM users
                WHERE id = :user_id
                """
            ),
            {"user_id": user_id},
        )
        await session.commit()


async def _get_reset_token_row(
    session_factory,
    *,
    user_id,
):
    async with session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT
                    id,
                    user_id,
                    token_hash,
                    expires_at,
                    used_at,
                    created_at
                FROM auth_password_reset_tokens
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"user_id": user_id},
        )
        return result.mappings().first()


async def _get_all_reset_token_rows(
    session_factory,
    *,
    user_id,
):
    async with session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT
                    id,
                    token_hash,
                    expires_at,
                    used_at,
                    created_at
                FROM auth_password_reset_tokens
                WHERE user_id = :user_id
                ORDER BY created_at ASC
                """
            ),
            {"user_id": user_id},
        )
        return result.mappings().all()


async def _get_password_hash(
    session_factory,
    *,
    user_id,
) -> str | None:
    async with session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT password_hash
                FROM user_credentials
                WHERE user_id = :user_id
                  AND credential_type = 'PASSWORD'
                LIMIT 1
                """
            ),
            {"user_id": user_id},
        )
        row = result.first()
        return row[0] if row else None


async def _get_session_state(
    session_factory,
    *,
    session_id,
):
    async with session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT
                    status,
                    is_revoked
                FROM user_sessions
                WHERE session_id = :session_id
                """
            ),
            {"session_id": session_id},
        )
        return result.first()


@pytest.mark.asyncio
async def test_real_postgresql_password_reset_token_persists_only_sha256_digest():
    engine, session_factory = _create_test_database()

    user_id = uuid4()
    raw_email = f"password-reset-{user_id}@example.invalid"
    username = f"password_reset_{user_id.hex[:12]}"

    try:
        await _create_test_user(
            session_factory,
            user_id=user_id,
            email=raw_email,
            username=username,
        )

        repository = PostgreSQLAuthenticationRepository(session_factory)

        raw_token = await repository.create_password_reset_token(
            user_id=user_id,
        )

        row = await _get_reset_token_row(
            session_factory,
            user_id=user_id,
        )

        assert row is not None

        expected_hash = sha256(
            raw_token.encode("utf-8")
        ).hexdigest()

        assert row["token_hash"] == expected_hash
        assert row["token_hash"] != raw_token
        assert len(row["token_hash"]) == 64

        assert row["expires_at"] is not None
        assert row["created_at"] is not None
        assert row["used_at"] is None

    finally:
        await _delete_test_data(
            session_factory,
            user_id=user_id,
        )
        await engine.dispose()


@pytest.mark.asyncio
async def test_real_postgresql_new_reset_token_supersedes_previous_unused_token():
    engine, session_factory = _create_test_database()

    user_id = uuid4()
    raw_email = f"password-reset-{user_id}@example.invalid"
    username = f"password_reset_{user_id.hex[:12]}"

    try:
        await _create_test_user(
            session_factory,
            user_id=user_id,
            email=raw_email,
            username=username,
        )

        repository = PostgreSQLAuthenticationRepository(session_factory)

        first_token = await repository.create_password_reset_token(
            user_id=user_id,
        )

        second_token = await repository.create_password_reset_token(
            user_id=user_id,
        )

        assert first_token != second_token

        rows = await _get_all_reset_token_rows(
            session_factory,
            user_id=user_id,
        )

        assert len(rows) == 2

        first_row = rows[0]
        second_row = rows[1]

        assert first_row["token_hash"] == sha256(
            first_token.encode("utf-8")
        ).hexdigest()
        assert second_row["token_hash"] == sha256(
            second_token.encode("utf-8")
        ).hexdigest()

        assert first_row["used_at"] is not None
        assert second_row["used_at"] is None

    finally:
        await _delete_test_data(
            session_factory,
            user_id=user_id,
        )
        await engine.dispose()


@pytest.mark.asyncio
async def test_real_postgresql_reset_changes_password_consumes_token_and_revokes_sessions():
    engine, session_factory = _create_test_database()

    user_id = uuid4()
    session_one = uuid4()
    session_two = uuid4()

    raw_email = f"password-reset-{user_id}@example.invalid"
    username = f"password_reset_{user_id.hex[:12]}"

    original_hash = "original-password-hash"
    replacement_hash = "replacement-password-hash"

    try:
        await _create_test_user(
            session_factory,
            user_id=user_id,
            email=raw_email,
            username=username,
        )

        await _create_test_credential(
            session_factory,
            user_id=user_id,
            password_hash=original_hash,
        )

        await _create_test_session(
            session_factory,
            user_id=user_id,
            session_id=session_one,
        )

        await _create_test_session(
            session_factory,
            user_id=user_id,
            session_id=session_two,
        )

        repository = PostgreSQLAuthenticationRepository(session_factory)

        raw_token = await repository.create_password_reset_token(
            user_id=user_id,
        )

        result = await repository.reset_password(
            token=raw_token,
            password_hash=replacement_hash,
        )

        assert result is True

        stored_hash = await _get_password_hash(
            session_factory,
            user_id=user_id,
        )

        assert stored_hash == replacement_hash
        assert stored_hash != original_hash

        row = await _get_reset_token_row(
            session_factory,
            user_id=user_id,
        )

        assert row is not None
        assert row["used_at"] is not None

        session_one_state = await _get_session_state(
            session_factory,
            session_id=session_one,
        )

        session_two_state = await _get_session_state(
            session_factory,
            session_id=session_two,
        )

        assert session_one_state is not None
        assert session_two_state is not None

        assert session_one_state.status == "revoked"
        assert session_one_state.is_revoked is True

        assert session_two_state.status == "revoked"
        assert session_two_state.is_revoked is True

        # The same raw token must now be unusable.
        second_attempt = await repository.reset_password(
            token=raw_token,
            password_hash="must-not-be-applied",
        )

        assert second_attempt is False

        final_hash = await _get_password_hash(
            session_factory,
            user_id=user_id,
        )

        assert final_hash == replacement_hash

    finally:
        await _delete_test_data(
            session_factory,
            user_id=user_id,
        )
        await engine.dispose()


@pytest.mark.asyncio
async def test_real_postgresql_expired_and_invalid_reset_tokens_are_rejected():
    engine, session_factory = _create_test_database()

    user_id = uuid4()
    raw_email = f"password-reset-{user_id}@example.invalid"
    username = f"password_reset_{user_id.hex[:12]}"

    original_hash = "original-password-hash"

    try:
        await _create_test_user(
            session_factory,
            user_id=user_id,
            email=raw_email,
            username=username,
        )

        await _create_test_credential(
            session_factory,
            user_id=user_id,
            password_hash=original_hash,
        )

        repository = PostgreSQLAuthenticationRepository(session_factory)

        expired_token = await repository.create_password_reset_token(
            user_id=user_id,
        )

        # Force this specific token into the expired state using the real DB.
        async with session_factory() as session:
            await session.execute(
                text(
                    """
                    UPDATE auth_password_reset_tokens
                    SET expires_at = :expired_at
                    WHERE user_id = :user_id
                    """
                ),
                {
                    "user_id": user_id,
                    "expired_at": datetime.now(timezone.utc)
                    - timedelta(minutes=1),
                },
            )
            await session.commit()

        expired_result = await repository.reset_password(
            token=expired_token,
            password_hash="must-not-be-applied",
        )

        assert expired_result is False

        invalid_result = await repository.reset_password(
            token="definitely-not-a-valid-reset-token",
            password_hash="must-not-be-applied",
        )

        assert invalid_result is False

        stored_hash = await _get_password_hash(
            session_factory,
            user_id=user_id,
        )

        assert stored_hash == original_hash

    finally:
        await _delete_test_data(
            session_factory,
            user_id=user_id,
        )
        await engine.dispose()


@pytest.mark.asyncio
async def test_real_postgresql_password_reset_context_returns_bound_email():
    engine, session_factory = _create_test_database()

    user_id = uuid4()
    raw_email = f"password-reset-context-{user_id}@example.invalid"
    username = f"password_reset_context_{user_id.hex[:12]}"

    try:
        await _create_test_user(
            session_factory,
            user_id=user_id,
            email=raw_email,
            username=username,
        )

        await _create_test_credential(
            session_factory,
            user_id=user_id,
            password_hash="context-password-hash",
        )

        repository = PostgreSQLAuthenticationRepository(session_factory)
        raw_token = await repository.create_password_reset_token(
            user_id=user_id,
        )

        context = await repository.get_password_reset_user(
            raw_token,
        )

        assert context is not None
        assert context.user_id == user_id
        assert context.email == raw_email
        assert context.password_hash == "context-password-hash"

    finally:
        await _delete_test_data(
            session_factory,
            user_id=user_id,
        )
        await engine.dispose()


@pytest.mark.asyncio
async def test_real_postgresql_reset_rejects_stale_expected_password_hash():
    engine, session_factory = _create_test_database()

    user_id = uuid4()
    raw_email = f"password-reset-stale-{user_id}@example.invalid"
    username = f"password_reset_stale_{user_id.hex[:12]}"
    original_hash = "original-password-hash"
    replacement_hash = "replacement-password-hash"

    try:
        await _create_test_user(
            session_factory,
            user_id=user_id,
            email=raw_email,
            username=username,
        )

        await _create_test_credential(
            session_factory,
            user_id=user_id,
            password_hash=original_hash,
        )

        repository = PostgreSQLAuthenticationRepository(session_factory)
        raw_token = await repository.create_password_reset_token(
            user_id=user_id,
        )

        async with session_factory() as session:
            await session.execute(
                text(
                    """
                    UPDATE user_credentials
                    SET password_hash = :password_hash
                    WHERE user_id = :user_id
                      AND credential_type = 'PASSWORD'
                    """
                ),
                {
                    "user_id": user_id,
                    "password_hash": "changed-by-concurrent-operation",
                },
            )
            await session.commit()

        result = await repository.reset_password(
            token=raw_token,
            password_hash=replacement_hash,
            expected_password_hash=original_hash,
        )

        assert result is False

        stored_hash = await _get_password_hash(
            session_factory,
            user_id=user_id,
        )
        assert stored_hash == "changed-by-concurrent-operation"

    finally:
        await _delete_test_data(
            session_factory,
            user_id=user_id,
        )
        await engine.dispose()
