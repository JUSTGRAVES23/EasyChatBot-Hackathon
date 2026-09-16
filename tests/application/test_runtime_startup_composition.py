"""
Runtime startup composition tests.

Validates application startup wiring.

Flow:

FastAPI Application
        |
        v
bootstrap_application
        |
        v
ExternalRuntimeContainer
        |
        v
ExternalRuntimeService


The test does not call:

- Parallel Search
- Gemini
- Google Cloud
- external providers
"""

from __future__ import annotations


import pytest


from application.bootstrap import (
    bootstrap_application,
    reset_bootstrap,
)

from runtime.external_runtime_container import (
    get_external_runtime_service,
)


@pytest.fixture(autouse=True)
def reset_runtime_state():
    """
    Ensure bootstrap state is isolated between tests.
    """

    reset_bootstrap()

    yield

    reset_bootstrap()


def test_bootstrap_registers_external_runtime_service():
    """
    Bootstrap should create and register
    ExternalRuntimeService.
    """

    bootstrap_application()

    service = (
        get_external_runtime_service()
    )

    assert service is not None


def test_bootstrap_is_idempotent():
    """
    Calling bootstrap twice must not recreate
    application runtime unexpectedly.
    """

    bootstrap_application()

    first_service = (
        get_external_runtime_service()
    )

    bootstrap_application()

    second_service = (
        get_external_runtime_service()
    )

    assert first_service is second_service
