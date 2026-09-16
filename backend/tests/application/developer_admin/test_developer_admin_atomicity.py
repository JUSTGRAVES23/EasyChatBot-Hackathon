from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.developer_admin.developer_admin_audit import (
    DeveloperAdminAuditEvent,
    DeveloperAdminAuditService,
)
from app.application.developer_admin.developer_admin_service import (
    DeveloperAdminLastAdminError,
    DeveloperAdminService,
)
from app.domain.authorization.permissions import Role
from app.domain.identity.principal import AccountStatus, Principal
from app.infrastructure.auth.postgresql_auth_repository import AuthUserRecord


def make_user(
    *,
    user_id=None,
    email="user@example.com",
    status="active",
    verified=True,
):
    return AuthUserRecord(
        id=user_id or uuid4(),
        email=email,
        username="user",
        status=status,
        email_verified=verified,
    )


class FakeUnitOfWork:
    def __init__(
        self,
        users=(),
        roles=None,
        *,
        fail_role=False,
        fail_audit=False,
    ):
        self.users = {u.id: u for u in users}
        self.roles = {
            uid: set(rs)
            for uid, rs in (roles or {}).items()
        }
        self.fail_role = fail_role
        self.fail_audit = fail_audit
        self.events = []
        self.committed = False
        self.rolled_back = False
        self._snapshot = None

    async def __aenter__(self):
        self._snapshot = {
            key: set(value)
            for key, value in self.roles.items()
        }
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        if exc_type is None:
            self.committed = True
        else:
            self.roles = {
                key: set(value)
                for key, value in self._snapshot.items()
            }
            self.rolled_back = True

    async def get_user(self, user_id):
        return self.users.get(user_id)

    async def get_user_roles(self, user_id):
        return tuple(self.roles.get(user_id, set()))

    async def count_users_with_role(self, role):
        return sum(
            role in roles
            for roles in self.roles.values()
        )

    async def add_user_role(self, *, user_id, role):
        if self.fail_role:
            raise RuntimeError("role mutation failed")

        roles = self.roles.setdefault(user_id, set())

        if role in roles:
            return False

        roles.add(role)
        return True

    async def remove_user_role(self, *, user_id, role):
        if self.fail_role:
            raise RuntimeError("role mutation failed")

        roles = self.roles.setdefault(user_id, set())

        if role not in roles:
            return False

        roles.remove(role)
        return True

    async def record_audit(
        self,
        event: DeveloperAdminAuditEvent,
    ):
        if self.fail_audit:
            raise RuntimeError("audit failed")

        self.events.append(event)
        return event


class FakeUnitOfWorkFactory:
    """Returns the supplied UoWs in order and records every creation."""

    def __init__(self, *unit_of_works):
        self.unit_of_works = list(unit_of_works)
        self.created = []

    def create(self):
        if not self.unit_of_works:
            raise AssertionError(
                "FakeUnitOfWorkFactory.create() was called "
                "more times than expected."
            )

        unit_of_work = self.unit_of_works.pop(0)
        self.created.append(unit_of_work)
        return unit_of_work


class FakeAuthRepository:
    def __init__(self, users=()):
        self.users = tuple(users)

    async def get_users_with_role(self, *, role):
        return tuple(self.users)


class FailingAuditService(DeveloperAdminAuditService):
    async def build_event(self, **kwargs):
        raise RuntimeError("audit construction failed")


def principal():
    return Principal(
        user_id=str(uuid4()),
        email="actor@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({Role.DEVELOPER_ADMIN.value}),
    )


@pytest.mark.asyncio
async def test_grant_role_and_audit_commit_together():
    target = make_user()

    uow = FakeUnitOfWork(
        users=(target,),
        roles={
            target.id: {
                Role.BETA_USER.value,
            },
        },
    )

    factory = FakeUnitOfWorkFactory(uow)

    service = DeveloperAdminService(
        FakeAuthRepository(),
        unit_of_work_factory=factory,
        audit_service=DeveloperAdminAuditService(),
    )

    await service.grant_developer_admin(
        actor=principal(),
        user_id=target.id,
    )

    assert Role.DEVELOPER_ADMIN.value in uow.roles[target.id]
    assert len(uow.events) == 1
    assert (
        uow.events[0].event_type
        == DeveloperAdminAuditService.GRANTED
    )
    assert uow.committed is True
    assert uow.rolled_back is False


@pytest.mark.asyncio
async def test_audit_failure_rolls_back_role():
    target = make_user()

    uow = FakeUnitOfWork(
        users=(target,),
        roles={
            target.id: {
                Role.BETA_USER.value,
            },
        },
        fail_audit=True,
    )

    factory = FakeUnitOfWorkFactory(uow)

    service = DeveloperAdminService(
        FakeAuthRepository(),
        unit_of_work_factory=factory,
        audit_service=DeveloperAdminAuditService(),
    )

    with pytest.raises(
        RuntimeError,
        match="audit failed",
    ):
        await service.grant_developer_admin(
            actor=principal(),
            user_id=target.id,
        )

    assert Role.DEVELOPER_ADMIN.value not in uow.roles[target.id]
    assert uow.committed is False
    assert uow.rolled_back is True


@pytest.mark.asyncio
async def test_role_failure_produces_no_audit():
    target = make_user()

    uow = FakeUnitOfWork(
        users=(target,),
        roles={
            target.id: {
                Role.BETA_USER.value,
            },
        },
        fail_role=True,
    )

    factory = FakeUnitOfWorkFactory(uow)

    service = DeveloperAdminService(
        FakeAuthRepository(),
        unit_of_work_factory=factory,
        audit_service=DeveloperAdminAuditService(),
    )

    with pytest.raises(
        RuntimeError,
        match="role mutation failed",
    ):
        await service.grant_developer_admin(
            actor=principal(),
            user_id=target.id,
        )

    assert Role.DEVELOPER_ADMIN.value not in uow.roles[target.id]
    assert uow.events == []
    assert uow.rolled_back is True


@pytest.mark.asyncio
async def test_last_admin_remains_protected():
    target = make_user()

    uow = FakeUnitOfWork(
        users=(target,),
        roles={
            target.id: {
                Role.DEVELOPER_ADMIN.value,
            },
        },
    )

    factory = FakeUnitOfWorkFactory(uow)

    service = DeveloperAdminService(
        FakeAuthRepository(),
        unit_of_work_factory=factory,
        audit_service=DeveloperAdminAuditService(),
    )

    with pytest.raises(DeveloperAdminLastAdminError):
        await service.revoke_developer_admin(
            actor=principal(),
            user_id=target.id,
        )

    assert Role.DEVELOPER_ADMIN.value in uow.roles[target.id]
    assert uow.events == []
    assert uow.committed is False
    assert uow.rolled_back is True


@pytest.mark.asyncio
async def test_idempotent_grant_does_not_create_false_audit_event():
    target = make_user()

    uow = FakeUnitOfWork(
        users=(target,),
        roles={
            target.id: {
                Role.DEVELOPER_ADMIN.value,
            },
        },
    )

    factory = FakeUnitOfWorkFactory(uow)

    service = DeveloperAdminService(
        FakeAuthRepository(),
        unit_of_work_factory=factory,
        audit_service=DeveloperAdminAuditService(),
    )

    await service.grant_developer_admin(
        actor=principal(),
        user_id=target.id,
    )

    assert len(uow.events) == 0
    assert Role.DEVELOPER_ADMIN.value in uow.roles[target.id]
    assert uow.committed is True


@pytest.mark.asyncio
async def test_revoke_role_and_audit_commit_together():
    target = make_user()
    other = make_user(email="other@example.com")

    uow = FakeUnitOfWork(
        users=(target, other),
        roles={
            target.id: {
                Role.DEVELOPER_ADMIN.value,
            },
            other.id: {
                Role.DEVELOPER_ADMIN.value,
            },
        },
    )

    factory = FakeUnitOfWorkFactory(uow)

    service = DeveloperAdminService(
        FakeAuthRepository(),
        unit_of_work_factory=factory,
        audit_service=DeveloperAdminAuditService(),
    )

    await service.revoke_developer_admin(
        actor=principal(),
        user_id=target.id,
    )

    assert Role.DEVELOPER_ADMIN.value not in uow.roles[target.id]
    assert len(uow.events) == 1
    assert (
        uow.events[0].event_type
        == DeveloperAdminAuditService.REVOKED
    )
    assert uow.committed is True


@pytest.mark.asyncio
async def test_two_operations_receive_different_uow_instances():
    first_target = make_user(
        email="first@example.com",
    )
    second_target = make_user(
        email="second@example.com",
    )

    first_uow = FakeUnitOfWork(
        users=(first_target,),
        roles={
            first_target.id: {
                Role.BETA_USER.value,
            },
        },
    )

    second_uow = FakeUnitOfWork(
        users=(second_target,),
        roles={
            second_target.id: {
                Role.BETA_USER.value,
            },
        },
    )

    factory = FakeUnitOfWorkFactory(
        first_uow,
        second_uow,
    )

    service = DeveloperAdminService(
        FakeAuthRepository(),
        unit_of_work_factory=factory,
        audit_service=DeveloperAdminAuditService(),
    )

    await service.grant_developer_admin(
        actor=principal(),
        user_id=first_target.id,
    )

    await service.grant_developer_admin(
        actor=principal(),
        user_id=second_target.id,
    )

    assert len(factory.created) == 2
    assert factory.created[0] is first_uow
    assert factory.created[1] is second_uow
    assert factory.created[0] is not factory.created[1]

    assert first_uow.committed is True
    assert second_uow.committed is True

    assert Role.DEVELOPER_ADMIN.value in (
        first_uow.roles[first_target.id]
    )
    assert Role.DEVELOPER_ADMIN.value in (
        second_uow.roles[second_target.id]
    )