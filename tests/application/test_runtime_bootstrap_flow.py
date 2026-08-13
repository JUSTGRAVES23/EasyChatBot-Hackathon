"""
Runtime bootstrap flow tests.

Validates:

FastAPI startup
        |
        v
Application Bootstrap
        |
        v
External Runtime Service
        |
        v
Configured Runtime dependency

No external providers are called.
"""


from __future__ import annotations


import pytest

from backend.application.bootstrap import (
    bootstrap_application,
    get_external_runtime_service,
)



def test_runtime_bootstrap_creates_service():
    """
    Application bootstrap must create
    ExternalRuntimeService.
    """

    bootstrap_application()

    service = (
        get_external_runtime_service()
    )

    assert service is not None



def test_runtime_bootstrap_is_reusable():
    """
    Bootstrap should be deterministic.

    Calling bootstrap twice must not break
    the application boundary.
    """

    bootstrap_application()

    first = (
        get_external_runtime_service()
    )

    bootstrap_application()

    second = (
        get_external_runtime_service()
    )

    assert first is not None
    assert second is not None