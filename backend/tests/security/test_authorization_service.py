from backend.app.application.authorization.authorization_service import (
    AuthenticationRequiredError,
    AuthorizationService,
    PermissionDeniedError,
)
from backend.app.domain.authorization.permissions import Permission
from backend.app.domain.identity.principal import (
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


def test_missing_identity_is_rejected():
    try:
        AuthorizationService().require_authenticated(None)
    except AuthenticationRequiredError:
        return

    raise AssertionError("Missing identity must be rejected.")
