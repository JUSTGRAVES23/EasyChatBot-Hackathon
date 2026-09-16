"""
External Runtime Container tests.

Validates the application dependency boundary.

Flow:

bootstrap
    |
    v
ExternalRuntimeContainer
    |
    v
ExternalRuntimeService


The container:

- stores configured services;
- returns configured services.

It does not:

- compose Runtime;
- create providers;
- create gateways;
- execute capabilities.
"""

from __future__ import annotations


import pytest


from runtime.external_runtime_container import (
    configure_external_runtime_service,
    get_external_runtime_service,
)

from services.external_runtime_service import (
    ExternalRuntimeService,
)


class FakeGateway:
    """
    Controlled gateway.
    """

    async def execute(
        self,
        request,
    ):
        return {
            "status": "completed",
        }


@pytest.fixture
def runtime_service():
    """
    Create controlled ExternalRuntimeService.
    """

    return ExternalRuntimeService(
        gateway=FakeGateway(),
    )


def test_container_stores_runtime_service(
    runtime_service,
):
    """
    Container should store configured service.
    """

    configure_external_runtime_service(
        runtime_service,
    )

    configured = (
        get_external_runtime_service()
    )

    assert configured is runtime_service


def test_container_rejects_none():
    """
    Container must reject invalid configuration.
    """

    with pytest.raises(ValueError):
        configure_external_runtime_service(
            None,
        )
