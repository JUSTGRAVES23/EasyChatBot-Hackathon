from app.application.authorization.authorization_service import (
    AuthenticationRequiredError,
    AuthorizationService,
    PermissionDeniedError,
)
from app.domain.authorization.permissions import Permission
from app.domain.identity.principal import (
    AccountStatus,
    Principal,
)


def operator() -> Principal:
    return Principal(
        user_id="operator-1",
        email="operator@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({"operator"}),
    )


def admin() -> Principal:
    return Principal(
        user_id="admin-1",
        email="admin@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({"admin"}),
    )


def beta_user() -> Principal:
    return Principal(
        user_id="beta-1",
        email="beta@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({"beta_user"}),
    )


def test_operator_can_publish_announcements():
    principal = AuthorizationService().require_permission(
        principal=operator(),
        permission=Permission.ANNOUNCEMENT_PUBLISH,
    )
    assert principal.user_id == "operator-1"


def test_beta_user_cannot_publish_announcements():
    try:
        AuthorizationService().require_permission(
            principal=beta_user(),
            permission=Permission.ANNOUNCEMENT_PUBLISH,
        )
    except PermissionDeniedError:
        return

    raise AssertionError("Beta users must not publish announcements.")


def test_operator_can_control_functionality():
    principal = AuthorizationService().require_permission(
        principal=operator(),
        permission=Permission.FUNCTIONALITY_CONTROL,
    )
    assert principal.user_id == "operator-1"


def test_admin_can_control_functionality():
    principal = AuthorizationService().require_permission(
        principal=admin(),
        permission=Permission.FUNCTIONALITY_CONTROL,
    )
    assert principal.user_id == "admin-1"


def test_beta_user_cannot_control_functionality():
    try:
        AuthorizationService().require_permission(
            principal=beta_user(),
            permission=Permission.FUNCTIONALITY_CONTROL,
        )
    except PermissionDeniedError:
        return

    raise AssertionError("Beta users must not control functionalities.")


def test_missing_identity_is_rejected():
    try:
        AuthorizationService().require_authenticated(None)
    except AuthenticationRequiredError:
        return

    raise AssertionError("Missing identity must be rejected.")

