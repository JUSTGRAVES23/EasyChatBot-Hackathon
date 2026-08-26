from __future__ import annotations

from enum import StrEnum


class Permission(StrEnum):
    ANNOUNCEMENT_VIEW = "announcement.view"
    ANNOUNCEMENT_PUBLISH = "announcement.publish"


class Role(StrEnum):
    BETA_USER = "beta_user"
    OPERATOR = "operator"
    ADMIN = "admin"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.BETA_USER: frozenset(),
    Role.OPERATOR: frozenset(
        {
            Permission.ANNOUNCEMENT_VIEW,
            Permission.ANNOUNCEMENT_PUBLISH,
        }
    ),
    Role.ADMIN: frozenset(
        {
            Permission.ANNOUNCEMENT_VIEW,
            Permission.ANNOUNCEMENT_PUBLISH,
        }
    ),
}


def has_permission(
    *,
    roles: frozenset[str],
    permission: Permission,
) -> bool:
    return any(
        permission in ROLE_PERMISSIONS.get(
            Role(raw_role),
            frozenset(),
        )
        for raw_role in roles
        if raw_role in {role.value for role in Role}
    )
