from app.application.provider_management.functionality_control_authorizer import (
    AuthorizationFunctionalityControlAuthorizer,
)
from app.domain.authorization.permissions import Permission
from app.domain.identity.principal import (
    AccountStatus,
    Principal,
)


def principal(*roles: str) -> Principal:
    return Principal(
        user_id="test-user",
        email="test@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset(roles),
    )


def test_operator_can_control_functionality():
    authorizer = AuthorizationFunctionalityControlAuthorizer()

    assert authorizer.can_control_functionality(
        actor=principal("operator"),
        environment="kids",
        functionality_id="conversation",
    )


def test_admin_can_control_functionality():
    authorizer = AuthorizationFunctionalityControlAuthorizer()

    assert authorizer.can_control_functionality(
        actor=principal("admin"),
        environment="adults",
        functionality_id="telegram",
    )


def test_beta_user_cannot_control_functionality():
    authorizer = AuthorizationFunctionalityControlAuthorizer()

    assert not authorizer.can_control_functionality(
        actor=principal("beta_user"),
        environment="kids",
        functionality_id="conversation",
    )


def test_non_principal_cannot_control_functionality():
    authorizer = AuthorizationFunctionalityControlAuthorizer()

    assert not authorizer.can_control_functionality(
        actor="operator",
        environment="kids",
        functionality_id="conversation",
    )

