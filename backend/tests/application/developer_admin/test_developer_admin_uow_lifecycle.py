from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from app.application.developer_admin.developer_admin_audit import (
    DeveloperAdminAuditService,
)
from app.application.developer_admin.developer_admin_service import (
    DeveloperAdminService,
)
from app.domain.authorization.permissions import Role
from app.domain.identity.principal import AccountStatus, Principal
from app.infrastructure.auth.postgresql_auth_repository import AuthUserRecord


def make_user(
    *,
    user_id: UUID | None = None,
    email: str = "user@example.com",
) -> AuthUserRecord:
    return AuthUserRecord(
        id=user_id or uuid4(),
        email=email,
        username="user",
        status="active",
        email_verified=True,
    )


def principal() -> Principal:
    return Principal(
        user_id=str(uuid4()),
        email="actor@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({Role.DEVELOPER_ADMIN.value}),
    )


@dataclass
class RecordingUnitOfWork:
    """
    Minimal application-level Unit of Work used to verify lifecycle
    isolation.

    Every UoW creates a new session marker when entered. The lifecycle
    tests therefore verify:

    1. each operation receives a different UoW instance;
    2. each UoW receives a different session instance;
    3. each operation completes its own UoW lifecycle independently.
    """

    users: dict[UUID, AuthUserRecord]
    roles: dict[UUID, set[str]] = field(default_factory=dict)

    session: object | None = None
    entered: bool = False
    committed: bool = False
    rolled_back: bool = False

    async def __aenter__(self) -> "RecordingUnitOfWork":
        self.session = object()
        self.entered = True
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        if exc_type is None:
            self.committed = True
        else:
            self.rolled_back = True

    async def get_user(
        self,
        user_id: UUID,
    ) -> AuthUserRecord | None:
        return self.users.get(user_id)

    async def get_user_roles(
        self,
        user_id: UUID,
    ) -> tuple[str, ...]:
        return tuple(self.roles.get(user_id, set()))

    async def count_users_with_role(
        self,
        role: str,
    ) -> int:
        return sum(
            1
            for user_roles in self.roles.values()
            if role in user_roles
        )

    async def add_user_role(
        self,
        *,
        user_id: UUID,
        role: str,
    ) -> bool:
        user_roles = self.roles.setdefault(
            user_id,
            set(),
        )

        if role in user_roles:
            return False

        user_roles.add(role)
        return True

    async def remove_user_role(
        self,
        *,
        user_id: UUID,
        role: str,
    ) -> bool:
        user_roles = self.roles.setdefault(
            user_id,
            set(),
        )

        if role not in user_roles:
            return False

        user_roles.remove(role)
        return True

    async def record_audit(
        self,
        event,
    ) -> object:
        return event


class RecordingUnitOfWorkFactory:
    """
    Test implementation of the Developer Admin UoW factory.

    Every call to create() must return a brand-new UoW instance.
    """

    def __init__(
        self,
        users: tuple[AuthUserRecord, ...],
    ) -> None:
        self.users = {
            user.id: user
            for user in users
        }

        self.created: list[RecordingUnitOfWork] = []

    def create(self) -> RecordingUnitOfWork:
        uow = RecordingUnitOfWork(
            users=self.users,
        )

        self.created.append(uow)

        return uow


class FakeAuthRepository:
    """
    Repository dependency required by DeveloperAdminService.

    The atomic production path performs the mutation through the injected
    Unit of Work.
    """

    async def get_users_with_role(
        self,
        *,
        role: str,
    ) -> tuple[AuthUserRecord, ...]:
        return ()


def create_service(
    factory: RecordingUnitOfWorkFactory,
) -> DeveloperAdminService:
    """
    Construct DeveloperAdminService using the complete atomic-path
    dependency contract.
    """

    return DeveloperAdminService(
        repository=FakeAuthRepository(),
        unit_of_work_factory=factory,
        audit_service=DeveloperAdminAuditService(),
    )


@pytest.mark.asyncio
async def test_each_operation_receives_a_fresh_uow_instance() -> None:
    first_target = make_user(
        email="first@example.com",
    )
    second_target = make_user(
        email="second@example.com",
    )

    factory = RecordingUnitOfWorkFactory(
        users=(
            first_target,
            second_target,
        ),
    )

    service = create_service(factory)

    actor = principal()

    await service.grant_developer_admin(
        actor=actor,
        user_id=first_target.id,
    )

    await service.grant_developer_admin(
        actor=actor,
        user_id=second_target.id,
    )

    assert len(factory.created) == 2

    first_uow = factory.created[0]
    second_uow = factory.created[1]

    assert first_uow is not second_uow

    assert first_uow.entered is True
    assert second_uow.entered is True


@pytest.mark.asyncio
async def test_each_operation_receives_a_fresh_session_instance() -> None:
    first_target = make_user(
        email="first@example.com",
    )
    second_target = make_user(
        email="second@example.com",
    )

    factory = RecordingUnitOfWorkFactory(
        users=(
            first_target,
            second_target,
        ),
    )

    service = create_service(factory)

    actor = principal()

    await service.grant_developer_admin(
        actor=actor,
        user_id=first_target.id,
    )

    await service.grant_developer_admin(
        actor=actor,
        user_id=second_target.id,
    )

    assert len(factory.created) == 2

    first_uow = factory.created[0]
    second_uow = factory.created[1]

    assert first_uow.session is not None
    assert second_uow.session is not None

    assert first_uow.session is not second_uow.session


@pytest.mark.asyncio
async def test_each_operation_enters_and_commits_its_own_uow() -> None:
    first_target = make_user(
        email="first@example.com",
    )
    second_target = make_user(
        email="second@example.com",
    )

    factory = RecordingUnitOfWorkFactory(
        users=(
            first_target,
            second_target,
        ),
    )

    service = create_service(factory)

    actor = principal()

    await service.grant_developer_admin(
        actor=actor,
        user_id=first_target.id,
    )

    await service.grant_developer_admin(
        actor=actor,
        user_id=second_target.id,
    )

    assert len(factory.created) == 2

    first_uow = factory.created[0]
    second_uow = factory.created[1]

    assert first_uow.entered is True
    assert second_uow.entered is True

    assert first_uow.committed is True
    assert second_uow.committed is True

    assert first_uow.rolled_back is False
    assert second_uow.rolled_back is False