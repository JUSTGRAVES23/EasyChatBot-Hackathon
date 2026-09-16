from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4


class DeveloperAdminAuditError(Exception):
    """Base error for Developer Administrator audit operations."""


class DeveloperAdminAuditValidationError(DeveloperAdminAuditError):
    """Raised when an audit event contains unsafe or invalid data."""


@dataclass(frozen=True, slots=True)
class DeveloperAdminAuditEvent:
    event_id: UUID
    event_type: str
    actor_user_id: UUID | None
    target_user_id: UUID
    actor_email: str | None
    target_email: str
    occurred_at: datetime
    correlation_id: str | None
    outcome: str
    metadata: tuple[tuple[str, str], ...] = ()
    actor_type: str = "user"


class DeveloperAdminAuditPort(Protocol):
    async def record(self, event: DeveloperAdminAuditEvent) -> DeveloperAdminAuditEvent: ...


class DeveloperAdminAuditService:
    """Creates validated security-audit events for Developer Admin changes."""

    GRANTED = "developer_admin.granted"
    REVOKED = "developer_admin.revoked"
    BOOTSTRAPPED = "developer_admin.bootstrap"

    SUCCESS = "success"
    FAILURE = "failure"

    ACTOR_USER = "user"
    ACTOR_BOOTSTRAP = "bootstrap"

    _FORBIDDEN_KEYS = frozenset(
        {
            "password",
            "password_hash",
            "token",
            "access_token",
            "refresh_token",
            "session",
            "cookie",
            "api_key",
            "secret",
            "database_url",
            "prompt",
            "model_response",
        }
    )

    def __init__(self, repository: DeveloperAdminAuditPort | None = None) -> None:
        self._repository = repository

    async def build_event(
        self,
        *,
        event_type: str,
        actor_user_id: UUID,
        target_user_id: UUID,
        actor_email: str,
        target_email: str,
        correlation_id: str | None = None,
        outcome: str = SUCCESS,
        metadata: dict[str, str] | None = None,
    ) -> DeveloperAdminAuditEvent:
        if event_type not in {self.GRANTED, self.REVOKED}:
            raise DeveloperAdminAuditValidationError(
                "Unsupported Developer Admin audit event type."
            )

        if outcome not in {self.SUCCESS, self.FAILURE}:
            raise DeveloperAdminAuditValidationError(
                "Unsupported Developer Admin audit outcome."
            )

        if not actor_email or not target_email:
            raise DeveloperAdminAuditValidationError(
                "Actor and target email are required for audit evidence."
            )

        safe_metadata = self._validate_metadata(metadata or {})

        return DeveloperAdminAuditEvent(
            event_id=uuid4(),
            event_type=event_type,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            actor_email=actor_email,
            target_email=target_email,
            occurred_at=datetime.now().astimezone(),
            correlation_id=correlation_id,
            outcome=outcome,
            metadata=tuple(sorted(safe_metadata.items())),
            actor_type=self.ACTOR_USER,
        )

    async def build_bootstrap_event(
        self,
        *,
        target_user_id: UUID,
        target_email: str,
        correlation_id: str | None = None,
    ) -> DeveloperAdminAuditEvent:
        if not target_email:
            raise DeveloperAdminAuditValidationError(
                "Target email is required for bootstrap audit evidence."
            )

        safe_metadata = self._validate_metadata(
            {
                "operation": "bootstrap",
                "mechanism": "controlled_backend_bootstrap",
            }
        )

        return DeveloperAdminAuditEvent(
            event_id=uuid4(),
            event_type=self.BOOTSTRAPPED,
            actor_user_id=None,
            target_user_id=target_user_id,
            actor_email=None,
            target_email=target_email,
            occurred_at=datetime.now().astimezone(),
            correlation_id=correlation_id,
            outcome=self.SUCCESS,
            metadata=tuple(sorted(safe_metadata.items())),
            actor_type=self.ACTOR_BOOTSTRAP,
        )

    async def record_change(self, **kwargs) -> DeveloperAdminAuditEvent:
        if self._repository is None:
            raise DeveloperAdminAuditError("Audit repository is required for persistence.")

        event = await self.build_event(**kwargs)
        return await self._repository.record(event)

    @classmethod
    def _validate_metadata(cls, metadata: dict[str, str]) -> dict[str, str]:
        if not isinstance(metadata, dict):
            raise DeveloperAdminAuditValidationError(
                "Audit metadata must be a dictionary."
            )

        safe: dict[str, str] = {}

        for key, value in metadata.items():
            normalized_key = str(key).strip().lower()

            if normalized_key in cls._FORBIDDEN_KEYS:
                raise DeveloperAdminAuditValidationError(
                    f"Unsafe audit metadata key: {normalized_key}."
                )

            if not normalized_key or len(normalized_key) > 100:
                raise DeveloperAdminAuditValidationError(
                    "Audit metadata key is invalid."
                )

            normalized_value = str(value)

            if len(normalized_value) > 1000:
                raise DeveloperAdminAuditValidationError(
                    "Audit metadata value is too long."
                )

            safe[normalized_key] = normalized_value

        return safe
