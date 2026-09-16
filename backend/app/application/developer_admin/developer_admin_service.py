from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.developer_admin.developer_admin_audit import (
    DeveloperAdminAuditService,
)
from app.application.developer_admin.developer_admin_uow import (
    DeveloperAdminUnitOfWork,
)
from app.application.developer_admin.developer_admin_uow_factory import (
    DeveloperAdminUnitOfWorkFactory,
)
from app.domain.authorization.permissions import Role
from app.domain.identity.principal import Principal
from app.infrastructure.auth.postgresql_auth_repository import (
    AuthUserRecord,
    PostgreSQLAuthenticationRepository,
)


class DeveloperAdminError(Exception):
    """Base error for Developer Administration operations."""


class DeveloperAdminUserNotFoundError(DeveloperAdminError):
    """Requested target user does not exist."""


class DeveloperAdminUserInactiveError(DeveloperAdminError):
    """Requested target user cannot receive Developer Admin privileges."""


class DeveloperAdminLastAdminError(DeveloperAdminError):
    """The final Developer Administrator cannot be removed."""


@dataclass(frozen=True, slots=True)
class DeveloperAdminRecord:
    user_id: UUID
    email: str
    username: str
    status: str
    email_verified: bool


class DeveloperAdminService:
    """Application boundary for controlled Developer Administrator management.

    Production composition injects a DeveloperAdminUnitOfWorkFactory.
    Each Developer Administrator mutation obtains a fresh Unit-of-Work
    instance from that factory so role mutations and their security audit
    evidence share one database transaction without sharing mutable UoW
    state between operations.

    The repository-only constructor path is retained for compatibility with
    existing isolated service tests. That compatibility path is deliberately
    not used by the production application.
    """

    ROLE = Role.DEVELOPER_ADMIN.value

    def __init__(
        self,
        repository: PostgreSQLAuthenticationRepository,
        *,
        unit_of_work_factory: DeveloperAdminUnitOfWorkFactory | None = None,
        audit_service: DeveloperAdminAuditService | None = None,
    ) -> None:
        if repository is None:
            raise ValueError("repository is required.")

        if (unit_of_work_factory is None) != (audit_service is None):
            raise ValueError(
                "unit_of_work_factory and audit_service must be supplied together."
            )

        self._repository = repository
        self._unit_of_work_factory = unit_of_work_factory
        self._audit_service = audit_service

    async def list_developer_administrators(
        self,
    ) -> tuple[DeveloperAdminRecord, ...]:
        users = await self._repository.get_users_with_role(
            role=self.ROLE,
        )

        return tuple(
            self._to_record(user)
            for user in users
        )

    async def grant_developer_admin(
        self,
        *,
        user_id: UUID,
        actor: Principal | None = None,
        correlation_id: str | None = None,
    ) -> DeveloperAdminRecord:
        # Production path: role mutation + audit share one transaction.
        if self._unit_of_work_factory is not None:
            if actor is None:
                raise ValueError(
                    "actor is required when using the atomic Developer Admin path."
                )

            return await self._grant_atomically(
                actor=actor,
                user_id=user_id,
                correlation_id=correlation_id,
            )

        # Compatibility path for existing isolated application tests.
        # Production composition never uses this path.
        return await self._grant_legacy(
            user_id=user_id,
        )

    async def revoke_developer_admin(
        self,
        *,
        user_id: UUID,
        actor: Principal | None = None,
        correlation_id: str | None = None,
    ) -> None:
        # Production path: role mutation + audit share one transaction.
        if self._unit_of_work_factory is not None:
            if actor is None:
                raise ValueError(
                    "actor is required when using the atomic Developer Admin path."
                )

            await self._revoke_atomically(
                actor=actor,
                user_id=user_id,
                correlation_id=correlation_id,
            )
            return

        # Compatibility path for existing isolated application tests.
        # Production composition never uses this path.
        await self._revoke_legacy(
            user_id=user_id,
        )

    async def _grant_atomically(
        self,
        *,
        actor: Principal,
        user_id: UUID,
        correlation_id: str | None,
    ) -> DeveloperAdminRecord:
        assert self._unit_of_work_factory is not None
        assert self._audit_service is not None

        # A fresh UoW is created for every Developer Admin operation.
        async with self._unit_of_work_factory.create() as uow:
            target = await uow.get_user(user_id)

            if target is None:
                raise DeveloperAdminUserNotFoundError(
                    "Target user does not exist."
                )

            if target.status != "active" or not target.email_verified:
                raise DeveloperAdminUserInactiveError(
                    "Developer Administrator privileges require an active, "
                    "verified user."
                )

            created = await uow.add_user_role(
                user_id=user_id,
                role=self.ROLE,
            )

            if created:
                event = await self._audit_service.build_event(
                    event_type=DeveloperAdminAuditService.GRANTED,
                    actor_user_id=UUID(actor.user_id),
                    target_user_id=target.id,
                    actor_email=actor.email,
                    target_email=target.email,
                    correlation_id=correlation_id,
                    metadata={"operation": "grant"},
                )

                await uow.record_audit(event)

            return self._to_record(target)

    async def _revoke_atomically(
        self,
        *,
        actor: Principal,
        user_id: UUID,
        correlation_id: str | None,
    ) -> None:
        assert self._unit_of_work_factory is not None
        assert self._audit_service is not None

        # A fresh UoW is created for every Developer Admin operation.
        async with self._unit_of_work_factory.create() as uow:
            target = await uow.get_user(user_id)

            if target is None:
                raise DeveloperAdminUserNotFoundError(
                    "Target user does not exist."
                )

            roles = await uow.get_user_roles(user_id)

            if self.ROLE not in roles:
                return

            current_count = await uow.count_users_with_role(
                role=self.ROLE,
            )

            if current_count <= 1:
                raise DeveloperAdminLastAdminError(
                    "The last Developer Administrator cannot be removed."
                )

            removed = await uow.remove_user_role(
                user_id=user_id,
                role=self.ROLE,
            )

            if removed:
                event = await self._audit_service.build_event(
                    event_type=DeveloperAdminAuditService.REVOKED,
                    actor_user_id=UUID(actor.user_id),
                    target_user_id=target.id,
                    actor_email=actor.email,
                    target_email=target.email,
                    correlation_id=correlation_id,
                    metadata={"operation": "revoke"},
                )

                await uow.record_audit(event)

    async def _grant_legacy(
        self,
        *,
        user_id: UUID,
    ) -> DeveloperAdminRecord:
        user = await self._repository.get_user_for_identity(user_id)

        if user is None:
            raise DeveloperAdminUserNotFoundError(
                "Target user does not exist."
            )

        if user.status != "active" or not user.email_verified:
            raise DeveloperAdminUserInactiveError(
                "Developer Administrator privileges require an active, "
                "verified user."
            )

        await self._repository.add_user_role(
            user_id=user_id,
            role=self.ROLE,
        )

        return self._to_record(user)

    async def _revoke_legacy(
        self,
        *,
        user_id: UUID,
    ) -> None:
        user = await self._repository.get_user_for_identity(user_id)

        if user is None:
            raise DeveloperAdminUserNotFoundError(
                "Target user does not exist."
            )

        current_count = await self._repository.count_users_with_role(
            role=self.ROLE,
        )

        roles = await self._repository.get_user_roles(user_id)

        if self.ROLE not in roles:
            return

        if current_count <= 1:
            raise DeveloperAdminLastAdminError(
                "The last Developer Administrator cannot be removed."
            )

        await self._repository.remove_user_role(
            user_id=user_id,
            role=self.ROLE,
        )

    @staticmethod
    def _to_record(
        user: AuthUserRecord,
    ) -> DeveloperAdminRecord:
        return DeveloperAdminRecord(
            user_id=user.id,
            email=user.email,
            username=user.username,
            status=user.status,
            email_verified=user.email_verified,
        )


__all__ = [
    "DeveloperAdminError",
    "DeveloperAdminLastAdminError",
    "DeveloperAdminRecord",
    "DeveloperAdminService",
    "DeveloperAdminUserInactiveError",
    "DeveloperAdminUserNotFoundError",
]