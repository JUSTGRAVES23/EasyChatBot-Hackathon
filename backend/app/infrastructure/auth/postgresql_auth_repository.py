from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass(frozen=True, slots=True)
class AuthUserRecord:
    id: UUID
    email: str
    username: str
    status: str
    email_verified: bool


@dataclass(frozen=True, slots=True)
class AuthCredentialRecord:
    user_id: UUID
    password_hash: str
    credential_type: str


@dataclass(frozen=True, slots=True)
class AuthSessionRecord:
    session_id: UUID
    user_id: UUID
    status: str
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime
    device_name: str | None
    ip_address: str | None
    is_revoked: bool
    metadata_json: dict


class PostgreSQLAuthenticationRepository:
    """PostgreSQL adapter for the existing EasyChatBot auth tables.

    The adapter intentionally uses SQLAlchemy Core statements rather than
    importing speculative ORM models. This binds the application contract to
    the inspected database schema while keeping persistence isolated.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        if session_factory is None:
            raise ValueError("session_factory is required.")
        self._session_factory = session_factory

    async def email_exists(self, email: str) -> bool:
        async with self._session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM users WHERE email = :email LIMIT 1"),
                {"email": email},
            )
            return result.first() is not None

    async def username_exists(self, username: str) -> bool:
        async with self._session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM users WHERE username = :username LIMIT 1"),
                {"username": username},
            )
            return result.first() is not None

    async def create_user(self, *, user_id: UUID, email: str, username: str) -> None:
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    text(
                        """
                        INSERT INTO users
                            (id, email, username, status, trial_status, created_at,
                             email_verified)
                        VALUES
                            (:id, :email, :username, 'active', 'not_started', :created_at,
                             FALSE)
                        """
                    ),
                    {
                        "id": user_id,
                        "email": email,
                        "username": username,
                        "created_at": now,
                    },
                )
                await session.execute(
                    text(
                        """
                        INSERT INTO auth_user_roles (user_id, role)
                        VALUES (:user_id, 'beta_user')
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {"user_id": user_id},
                )

    async def create_password_credential(self, *, user_id: UUID, password_hash: str) -> None:
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    text(
                        """
                        INSERT INTO user_credentials
                            (id, user_id, password_hash, credential_type,
                             created_at, updated_at)
                        VALUES
                            (:id, :user_id, :password_hash, 'PASSWORD',
                             :created_at, :updated_at)
                        """
                    ),
                    {
                        "id": __import__("uuid").uuid4(),
                        "user_id": user_id,
                        "password_hash": password_hash,
                        "created_at": now,
                        "updated_at": now,
                    },
                )

    async def create_email_verification(self, *, user_id: UUID, email: str) -> str:
        """Create a one-time verification token.

        The raw token is returned to the application boundary. Only its SHA-256
        digest is persisted. Delivery is deliberately outside this repository.
        """
        import hashlib
        import secrets

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)
        verification_id = __import__("uuid").uuid4()

        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    text(
                        """
                        INSERT INTO auth_email_verification_tokens
                            (id, user_id, email, token_hash, expires_at, created_at)
                        VALUES
                            (:id, :user_id, :email, :token_hash,
                             :expires_at, :created_at)
                        """
                    ),
                    {
                        "id": verification_id,
                        "user_id": user_id,
                        "email": email,
                        "token_hash": token_hash,
                        "expires_at": now + timedelta(hours=24),
                        "created_at": now,
                    },
                )
        return raw_token

    async def verify_email(self, token: str) -> bool:
        import hashlib

        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)

        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    text(
                        """
                        SELECT id, user_id
                        FROM auth_email_verification_tokens
                        WHERE token_hash = :token_hash
                          AND used_at IS NULL
                          AND expires_at > :now
                        FOR UPDATE
                        """
                    ),
                    {"token_hash": token_hash, "now": now},
                )
                row = result.mappings().first()
                if row is None:
                    return False

                await session.execute(
                    text(
                        "UPDATE users SET email_verified = TRUE WHERE id = :user_id"
                    ),
                    {"user_id": row["user_id"]},
                )
                await session.execute(
                    text(
                        "UPDATE auth_email_verification_tokens SET used_at = :now WHERE id = :id"
                    ),
                    {"now": now, "id": row["id"]},
                )
                return True

    async def get_user_by_email(self, email: str) -> AuthUserRecord | None:
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT id, email, username, status, email_verified
                    FROM users
                    WHERE email = :email
                    LIMIT 1
                    """
                ),
                {"email": email},
            )
            row = result.mappings().first()
            return self._user(row) if row else None

    async def get_password_credential(self, user_id: UUID) -> AuthCredentialRecord | None:
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT user_id, password_hash, credential_type
                    FROM user_credentials
                    WHERE user_id = :user_id AND credential_type = 'PASSWORD'
                    LIMIT 1
                    """
                ),
                {"user_id": user_id},
            )
            row = result.mappings().first()
            if row is None:
                return None
            return AuthCredentialRecord(
                user_id=row["user_id"],
                password_hash=row["password_hash"],
                credential_type=row["credential_type"],
            )

    async def create_session(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        created_at: datetime,
        expires_at: datetime,
        device_name: str | None,
        ip_address: str | None,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    text(
                        """
                        INSERT INTO user_sessions
                            (session_id, user_id, status, created_at, expires_at,
                             last_activity_at, device_name, ip_address,
                             is_revoked, metadata_json)
                        VALUES
                            (:session_id, :user_id, 'active', :created_at, :expires_at,
                             :last_activity_at, :device_name, :ip_address,
                             FALSE, CAST(:metadata_json AS JSON))
                        """
                    ),
                    {
                        "session_id": session_id,
                        "user_id": user_id,
                        "created_at": created_at,
                        "expires_at": expires_at,
                        "last_activity_at": created_at,
                        "device_name": device_name,
                        "ip_address": ip_address,
                        "metadata_json": "{}",
                    },
                )

    async def get_session(self, session_id: str | UUID) -> AuthSessionRecord | None:
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT session_id, user_id, status, created_at, expires_at,
                           last_activity_at, device_name, ip_address,
                           is_revoked, metadata_json
                    FROM user_sessions
                    WHERE session_id = :session_id
                    LIMIT 1
                    """
                ),
                {"session_id": session_id},
            )
            row = result.mappings().first()
            if row is None:
                return None
            return AuthSessionRecord(
                session_id=row["session_id"],
                user_id=row["user_id"],
                status=row["status"],
                created_at=row["created_at"],
                expires_at=row["expires_at"],
                last_activity_at=row["last_activity_at"],
                device_name=row["device_name"],
                ip_address=row["ip_address"],
                is_revoked=bool(row["is_revoked"]),
                metadata_json=row["metadata_json"] or {},
            )

    async def revoke_session(self, session_id: UUID) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    text(
                        """
                        UPDATE user_sessions
                        SET is_revoked = TRUE, status = 'revoked'
                        WHERE session_id = :session_id
                        """
                    ),
                    {"session_id": session_id},
                )

    async def get_user_for_identity(self, user_id: UUID) -> AuthUserRecord | None:
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT id, email, username, status, email_verified
                    FROM users
                    WHERE id = :user_id
                    LIMIT 1
                    """
                ),
                {"user_id": user_id},
            )
            row = result.mappings().first()
            return self._user(row) if row else None

    async def get_user_roles(self, user_id: UUID) -> tuple[str, ...]:
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    "SELECT role FROM auth_user_roles WHERE user_id = :user_id ORDER BY role"
                ),
                {"user_id": user_id},
            )
            return tuple(row[0] for row in result.all())

    @staticmethod
    def _user(row) -> AuthUserRecord:
        return AuthUserRecord(
            id=row["id"],
            email=row["email"],
            username=row["username"],
            status=row["status"],
            email_verified=bool(row["email_verified"]),
        )
