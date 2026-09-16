from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.developer_admin.developer_admin_service import (
    DeveloperAdminLastAdminError,
    DeveloperAdminRecord,
    DeveloperAdminService,
    DeveloperAdminUserInactiveError,
    DeveloperAdminUserNotFoundError,
)
from app.domain.authorization.permissions import Role
from app.infrastructure.auth.postgresql_auth_repository import AuthUserRecord


class FakeDeveloperAdminRepository:
    def __init__(
        self,
        *,
        users: tuple[AuthUserRecord, ...] = (),
        roles: dict | None = None,
    ) -> None:
        self.users = {
            user.id: user
            for user in users
        }

        self.roles = {
            user_id: set(user_roles)
            for user_id, user_roles in (roles or {}).items()
        }

    async def get_users_with_role(
        self,
        *,
        role: str,
    ) -> tuple[AuthUserRecord, ...]:
        return tuple(
            user
            for user in self.users.values()
            if role in self.roles.get(user.id, set())
        )

    async def get_user_for_identity(
        self,
        user_id,
    ) -> AuthUserRecord | None:
        return self.users.get(user_id)

    async def add_user_role(
        self,
        *,
        user_id,
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
        user_id,
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

    async def count_users_with_role(
        self,
        *,
        role: str,
    ) -> int:
        return sum(
            role in user_roles
            for user_roles in self.roles.values()
        )

    async def get_user_roles(
        self,
        user_id,
    ) -> frozenset[str]:
        return frozenset(
            self.roles.get(
                user_id,
                set(),
            )
        )


def make_user(
    *,
    user_id=None,
    email: str = "user@example.com",
    username: str = "user",
    status: str = "active",
    email_verified: bool = True,
) -> AuthUserRecord:
    return AuthUserRecord(
        id=user_id or uuid4(),
        email=email,
        username=username,
        status=status,
        email_verified=email_verified,
    )


@pytest.mark.asyncio
async def test_list_developer_administrators_returns_only_developer_admins():
    admin = make_user(
        email="admin@example.com",
        username="admin",
    )

    normal_user = make_user(
        email="user@example.com",
        username="user",
    )

    repository = FakeDeveloperAdminRepository(
        users=(
            admin,
            normal_user,
        ),
        roles={
            admin.id: {
                Role.DEVELOPER_ADMIN.value,
            },
            normal_user.id: {
                Role.BETA_USER.value,
            },
        },
    )

    service = DeveloperAdminService(repository)

    result = await service.list_developer_administrators()

    assert result == (
        DeveloperAdminRecord(
            user_id=admin.id,
            email=admin.email,
            username=admin.username,
            status=admin.status,
            email_verified=admin.email_verified,
        ),
    )


@pytest.mark.asyncio
async def test_grant_developer_admin_requires_existing_user():
    repository = FakeDeveloperAdminRepository()

    service = DeveloperAdminService(repository)

    user_id = uuid4()

    with pytest.raises(DeveloperAdminUserNotFoundError):
        await service.grant_developer_admin(
            user_id=user_id,
        )


@pytest.mark.asyncio
async def test_grant_developer_admin_requires_active_verified_user():
    inactive_user = make_user(
        status="inactive",
        email_verified=True,
    )

    repository = FakeDeveloperAdminRepository(
        users=(inactive_user,),
    )

    service = DeveloperAdminService(repository)

    with pytest.raises(DeveloperAdminUserInactiveError):
        await service.grant_developer_admin(
            user_id=inactive_user.id,
        )


@pytest.mark.asyncio
async def test_grant_developer_admin_requires_verified_email():
    unverified_user = make_user(
        status="active",
        email_verified=False,
    )

    repository = FakeDeveloperAdminRepository(
        users=(unverified_user,),
    )

    service = DeveloperAdminService(repository)

    with pytest.raises(DeveloperAdminUserInactiveError):
        await service.grant_developer_admin(
            user_id=unverified_user.id,
        )


@pytest.mark.asyncio
async def test_grant_developer_admin_assigns_role():
    user = make_user()

    repository = FakeDeveloperAdminRepository(
        users=(user,),
        roles={
            user.id: {
                Role.BETA_USER.value,
            },
        },
    )

    service = DeveloperAdminService(repository)

    result = await service.grant_developer_admin(
        user_id=user.id,
    )

    assert result.user_id == user.id
    assert result.email == user.email
    assert (
        Role.DEVELOPER_ADMIN.value
        in repository.roles[user.id]
    )


@pytest.mark.asyncio
async def test_grant_developer_admin_is_idempotent():
    user = make_user()

    repository = FakeDeveloperAdminRepository(
        users=(user,),
        roles={
            user.id: {
                Role.BETA_USER.value,
                Role.DEVELOPER_ADMIN.value,
            },
        },
    )

    service = DeveloperAdminService(repository)

    result = await service.grant_developer_admin(
        user_id=user.id,
    )

    assert result.user_id == user.id

    assert repository.roles[user.id] == {
        Role.BETA_USER.value,
        Role.DEVELOPER_ADMIN.value,
    }


@pytest.mark.asyncio
async def test_revoke_developer_admin_requires_existing_user():
    repository = FakeDeveloperAdminRepository()

    service = DeveloperAdminService(repository)

    with pytest.raises(DeveloperAdminUserNotFoundError):
        await service.revoke_developer_admin(
            user_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_revoke_non_admin_is_idempotent():
    user = make_user()

    repository = FakeDeveloperAdminRepository(
        users=(user,),
        roles={
            user.id: {
                Role.BETA_USER.value,
            },
        },
    )

    service = DeveloperAdminService(repository)

    await service.revoke_developer_admin(
        user_id=user.id,
    )

    assert repository.roles[user.id] == {
        Role.BETA_USER.value,
    }


@pytest.mark.asyncio
async def test_revoke_prevents_removing_last_developer_admin():
    user = make_user()

    repository = FakeDeveloperAdminRepository(
        users=(user,),
        roles={
            user.id: {
                Role.BETA_USER.value,
                Role.DEVELOPER_ADMIN.value,
            },
        },
    )

    service = DeveloperAdminService(repository)

    with pytest.raises(DeveloperAdminLastAdminError):
        await service.revoke_developer_admin(
            user_id=user.id,
        )

    assert (
        Role.DEVELOPER_ADMIN.value
        in repository.roles[user.id]
    )


@pytest.mark.asyncio
async def test_revoke_developer_admin_when_multiple_admins_exist():
    first_admin = make_user(
        email="admin1@example.com",
        username="admin1",
    )

    second_admin = make_user(
        email="admin2@example.com",
        username="admin2",
    )

    repository = FakeDeveloperAdminRepository(
        users=(
            first_admin,
            second_admin,
        ),
        roles={
            first_admin.id: {
                Role.DEVELOPER_ADMIN.value,
            },
            second_admin.id: {
                Role.DEVELOPER_ADMIN.value,
            },
        },
    )

    service = DeveloperAdminService(repository)

    await service.revoke_developer_admin(
        user_id=first_admin.id,
    )

    assert (
        Role.DEVELOPER_ADMIN.value
        not in repository.roles[first_admin.id]
    )

    assert (
        Role.DEVELOPER_ADMIN.value
        in repository.roles[second_admin.id]
    )