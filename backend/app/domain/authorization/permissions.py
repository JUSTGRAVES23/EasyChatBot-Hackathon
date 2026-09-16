from __future__ import annotations

from enum import StrEnum


class Permission(StrEnum):
    ANNOUNCEMENT_VIEW = "announcement.view"
    ANNOUNCEMENT_PUBLISH = "announcement.publish"
    FUNCTIONALITY_CONTROL = "functionality.control"
    INTERNAL_DATA_READ = "internal_data.read"
    DEVELOPER_ADMIN_MANAGE = "developer_admin.manage"


class Role(StrEnum):
    BETA_USER = "beta_user"
    OPERATOR = "operator"
    ADMIN = "admin"
    DEVELOPER_ADMIN = "developer_admin"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.BETA_USER: frozenset(),

    Role.OPERATOR: frozenset(
        {
            Permission.ANNOUNCEMENT_VIEW,
            Permission.ANNOUNCEMENT_PUBLISH,
            Permission.FUNCTIONALITY_CONTROL,
            Permission.INTERNAL_DATA_READ,
        }
    ),

    Role.ADMIN: frozenset(
        {
            Permission.ANNOUNCEMENT_VIEW,
            Permission.ANNOUNCEMENT_PUBLISH,
            Permission.FUNCTIONALITY_CONTROL,
            Permission.INTERNAL_DATA_READ,
        }
    ),

    Role.DEVELOPER_ADMIN: frozenset(
        {
            Permission.DEVELOPER_ADMIN_MANAGE,
        }
    ),
}


def has_permission(
    *,
    roles: frozenset[str],
    permission: Permission,
) -> bool:
    valid_roles = {role.value for role in Role}

    return any(
        permission in ROLE_PERMISSIONS.get(
            Role(raw_role),
            frozenset(),
        )
        for raw_role in roles
        if raw_role in valid_roles
    )