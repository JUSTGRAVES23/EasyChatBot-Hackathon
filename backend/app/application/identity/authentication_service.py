from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
import hashlib
import hmac
import secrets
import logging


logger = logging.getLogger(__name__)


class AuthenticationError(ValueError):
    """Expected authentication failure."""


@dataclass(frozen=True, slots=True)
class SessionResult:
    session_id: UUID
    user_id: UUID
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class PasswordResetContext:
    """Safe reset-link context exposed to the frontend."""

    email: str


class PasswordHasher:
    """PBKDF2 password hashing using the Python standard library."""

    algorithm = "pbkdf2_sha256"
    iterations = 600_000
    salt_bytes = 32

    def hash(self, password: str) -> str:
        if len(password) < 12:
            raise AuthenticationError(
                "Password must contain at least 12 characters."
            )

        salt = secrets.token_bytes(self.salt_bytes)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self.iterations,
        )

        return (
            f"{self.algorithm}${self.iterations}$"
            f"{salt.hex()}${digest.hex()}"
        )

    def verify(self, password: str, encoded: str) -> bool:
        try:
            algorithm, iterations, salt_hex, digest_hex = encoded.split("$")

            if algorithm != self.algorithm:
                return False

            candidate = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt_hex),
                int(iterations),
            )

            return hmac.compare_digest(
                candidate.hex(),
                digest_hex,
            )
        except (ValueError, TypeError):
            return False


class AuthenticationService:
    """Application service for registration/login/session lifecycle.

    Persistence is supplied through a repository protocol so the service does
    not depend on a particular ORM implementation.

    Authentication email delivery is supplied through the application email
    service boundary. Provider selection and provider credentials remain
    outside this service.
    """

    def __init__(
        self,
        repository,
        *,
        email_service=None,
        password_hasher: PasswordHasher | None = None,
        session_ttl: timedelta = timedelta(hours=12),
    ) -> None:
        self._repository = repository
        self._email_service = email_service
        self._password_hasher = password_hasher or PasswordHasher()
        self._session_ttl = session_ttl

    async def register(
        self,
        *,
        email: str,
        username: str,
        password: str,
    ):
        normalized_email = email.strip().lower()
        normalized_username = username.strip()

        if not normalized_email or "@" not in normalized_email:
            raise AuthenticationError("A valid email is required.")

        if not normalized_username:
            raise AuthenticationError("Username is required.")

        if await self._repository.email_exists(normalized_email):
            raise AuthenticationError(
                "An account with this email already exists."
            )

        if await self._repository.username_exists(normalized_username):
            raise AuthenticationError(
                "That username is already in use."
            )

        user_id = uuid4()
        password_hash = self._password_hasher.hash(password)

        await self._repository.create_user(
            user_id=user_id,
            email=normalized_email,
            username=normalized_username,
        )

        await self._repository.create_password_credential(
            user_id=user_id,
            password_hash=password_hash,
        )

        verification_token = (
            await self._repository.create_email_verification(
                user_id=user_id,
                email=normalized_email,
            )
        )

        if self._email_service is None:
            raise AuthenticationError(
                "Registration email delivery is not configured."
            )

        try:
            await self._email_service.send_verification_email(
                email=normalized_email,
                username=normalized_username,
                verification_token=verification_token,
            )
        except Exception:
            raise AuthenticationError(
                "Registration email could not be sent. "
                "Please try again later."
            ) from None

        return user_id

    async def authenticate(
        self,
        *,
        email: str,
        password: str,
        device_name: str | None = None,
        ip_address: str | None = None,
    ) -> SessionResult:
        user = await self._repository.get_user_by_email(
            email.strip().lower()
        )

        if user is None:
            raise AuthenticationError(
                "Invalid email or password."
            )

        if user.status != "active":
            raise AuthenticationError(
                "Account is not active."
            )

        if not user.email_verified:
            raise AuthenticationError(
                "Email verification is required."
            )

        credential = await self._repository.get_password_credential(
            user.id
        )

        if credential is None or not self._password_hasher.verify(
            password,
            credential.password_hash,
        ):
            raise AuthenticationError(
                "Invalid email or password."
            )

        now = datetime.now(timezone.utc)
        expires_at = now + self._session_ttl
        session_id = uuid4()

        await self._repository.create_session(
            session_id=session_id,
            user_id=user.id,
            created_at=now,
            expires_at=expires_at,
            device_name=device_name,
            ip_address=ip_address,
        )

        return SessionResult(
            session_id=session_id,
            user_id=user.id,
            expires_at=expires_at,
        )

    async def request_password_reset(
        self,
        *,
        email: str,
    ) -> None:
        """Request a password-reset email without revealing account existence.

        Unknown accounts intentionally produce the same successful outcome as
        known accounts. Reset-token generation and persistence remain inside
        the repository, while email delivery remains inside the email service.
        """
        normalized_email = email.strip().lower()

        if not normalized_email or "@" not in normalized_email:
            raise AuthenticationError("A valid email is required.")

        user = await self._repository.get_user_by_email(
            normalized_email,
        )

        # Do not reveal whether the account exists.
        if user is None:
            return

        now = datetime.now(timezone.utc)
        rate_limit_since = now - timedelta(hours=1)

        recent_requests = (
            await self._repository.count_recent_password_reset_tokens(
                user_id=user.id,
                since=rate_limit_since,
            )
        )

        # Maximum of three reset requests per account per hour.
        if recent_requests >= 3:
            return

        reset_token = await self._repository.create_password_reset_token(
            user_id=user.id,
        )

        if self._email_service is None:
            raise AuthenticationError(
                "Password reset email delivery is not configured."
            )

        await self._email_service.send_password_reset_email(
            email=user.email,
            username=user.username,
            reset_token=reset_token,
        )

    async def get_password_reset_context(
        self,
        *,
        token: str,
    ) -> PasswordResetContext:
        """Return safe account context for a valid reset token.

        The raw token is used only for transient lookup. The repository
        validates its digest, expiry and single-use state. No credential
        material is exposed to the caller.
        """
        normalized_token = token.strip()

        if not normalized_token:
            raise AuthenticationError(
                "Password reset token is required."
            )

        context = await self._repository.get_password_reset_context(
            token=normalized_token,
        )

        if context is None:
            raise AuthenticationError(
                "Invalid or expired password reset token."
            )

        return PasswordResetContext(
            email=context.email,
        )

    @staticmethod
    def _validate_password_reset_password(
        password: str,
    ) -> None:
        """Enforce the reset-specific password policy."""
        if len(password) < 12:
            raise AuthenticationError(
                "Password must contain at least 12 characters."
            )

        if not any(character.isupper() for character in password):
            raise AuthenticationError(
                "Password must contain at least one uppercase letter."
            )

        if not any(character.islower() for character in password):
            raise AuthenticationError(
                "Password must contain at least one lowercase letter."
            )

        if not any(character.isdigit() for character in password):
            raise AuthenticationError(
                "Password must contain at least one number."
            )

        if not any(
            not character.isalnum()
            for character in password
        ):
            raise AuthenticationError(
                "Password must contain at least one special character."
            )

    async def confirm_password_reset(
        self,
        *,
        token: str,
        new_password: str,
    ) -> None:
        """Set a new password using a valid one-time reset token."""
        normalized_token = token.strip()

        if not normalized_token:
            raise AuthenticationError(
                "Password reset token is required."
            )

        context = await self._repository.get_password_reset_context(
            token=normalized_token,
        )

        if context is None:
            raise AuthenticationError(
                "Invalid or expired password reset token."
            )

        self._validate_password_reset_password(new_password)

        if self._password_hasher.verify(
            new_password,
            context.password_hash,
        ):
            raise AuthenticationError(
                "New password must be different from your previous password."
            )

        password_hash = self._password_hasher.hash(new_password)

        reset = await self._repository.reset_password(
            token=normalized_token,
            password_hash=password_hash,
            expected_password_hash=context.password_hash,
        )

        if not reset:
            raise AuthenticationError(
                "Invalid or expired password reset token."
            )

        # The password transaction has succeeded. Confirmation email delivery
        # is deliberately best-effort: a provider outage must not turn a
        # successful password change into a misleading API failure. The
        # timestamp below is the application-level confirmation time and is
        # rendered by the email service in UTC.
        reset_at = datetime.now(timezone.utc)

        if self._email_service is not None:
            try:
                await self._email_service.send_password_reset_confirmation_email(
                    email=context.email,
                    username=context.email,
                    reset_at=reset_at,
                )
            except Exception:
                logger.exception(
                    "Password reset confirmation email delivery failed."
                )

    async def verify_email(
        self,
        token: str,
    ) -> None:
        """Verify an application email address using a repository-managed token.

        Token validation, expiration and single-use enforcement remain inside
        the authentication repository.
        """
        normalized_token = token.strip()

        if not normalized_token:
            raise AuthenticationError(
                "Email verification token is required."
            )

        verified = await self._repository.verify_email(
            normalized_token,
        )

        if not verified:
            raise AuthenticationError(
                "Invalid or expired email verification token."
            )

    async def revoke_session(
        self,
        session_id: UUID,
    ) -> None:
        await self._repository.revoke_session(session_id)