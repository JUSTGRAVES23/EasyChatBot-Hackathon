"""
Tests External Runtime Container.

Validates:

Application Bootstrap
        |
        v
External Runtime Container
        |
        v
ExternalRuntimeService

The test uses controlled dependencies.

No external providers are called.
"""

from __future__ import annotations

import pytest

from backend.runtime.external_runtime_container import (
    configure_external_runtime_service,
    get_external_runtime_service,
)

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)


class FakeGateway:
    """
    Controlled Runtime gateway.
    """

    async def execute(
        self,
        request,
    ):
        return None


def test_container_registers_runtime_service():
    """
    Configured service should be retrievable.
    """

    service = ExternalRuntimeService(
        gateway=FakeGateway(),
    )

    configure_external_runtime_service(
        service,
    )

    result = get_external_runtime_service()

    assert result is service


def test_container_rejects_missing_service():
    """
    Container should reject invalid configuration.
    """

    with pytest.raises(
        ValueError,
        match="ExternalRuntimeService cannot be None",
    ):
        configure_external_runtime_service(
            None,
        )