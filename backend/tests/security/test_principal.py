from app.domain.identity.principal import (
    AccountStatus,
    Principal,
)


def test_principal_requires_verified_active_identity():
    principal = Principal(
        user_id="u1",
        email="user@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
    )

    assert principal.is_active is True


def test_unverified_principal_is_not_active():
    principal = Principal(
        user_id="u1",
        email="user@example.com",
        email_verified=False,
        account_status=AccountStatus.ACTIVE,
    )

    assert principal.is_active is False

