"""
Authentication application-composition architecture regression tests.

These tests protect the authentication boundary used by the application
composition.

The tests intentionally verify composition/contracts rather than provider
implementation details.
"""

from __future__ import annotations

import importlib


def test_identity_application_package_is_importable() -> None:
    """The active identity application package must be importable."""
    module = importlib.import_module("app.application.identity")

    assert module is not None


def test_identity_provider_is_importable_from_application_boundary() -> None:
    """
    Authentication provider abstractions must remain behind the application
    identity boundary.
    """
    module = importlib.import_module(
        "app.application.identity.identity_provider"
    )

    assert hasattr(module, "IdentityProvider")


def test_application_entrypoint_imports_without_authentication_composition_error() -> None:
    """
    The primary application composition must be importable without breaking
    at the authentication boundary.
    """
    module = importlib.import_module("app.main")

    assert hasattr(module, "create_application")
