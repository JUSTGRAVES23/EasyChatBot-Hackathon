from __future__ import annotations

from app.application.identity.authentication_service import (
    AuthenticationError,
    PasswordHasher,
)


def test_password_hash_round_trip() -> None:
    hasher = PasswordHasher()

    encoded = hasher.hash("A sufficiently strong password!")

    assert encoded != "A sufficiently strong password!"
    assert hasher.verify(
        "A sufficiently strong password!",
        encoded,
    )
    assert not hasher.verify(
        "wrong password",
        encoded,
    )


def test_short_password_rejected() -> None:
    hasher = PasswordHasher()

    try:
        hasher.hash("short")
    except AuthenticationError:
        pass
    else:
        raise AssertionError("Short password was accepted.")

