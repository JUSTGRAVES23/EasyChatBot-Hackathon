"""
Application Factory Runtime tests.

Validates:

ApplicationFactory
        |
        v
RuntimeApplicationService
        |
        v
ExternalRuntimeService


The factory:

- creates application services;
- injects dependencies.

It does not:

- create providers;
- create agents;
- create gateways;
- execute capabilities.
"""

from __future__ import annotations


import pytest


from backend.application.factory import (
    ApplicationFactory,
)

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)

from backend.services.runtime.runtime_application_service import (
    RuntimeApplicationService,
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
            "request_id": "factory-test",
            "capability": request.capability,
            "status": "completed",
            "output": {},
        }


def test_factory_creates_external_runtime_service():
    """
    Factory should create ExternalRuntimeService
    from an existing gateway.
    """

    factory = ApplicationFactory()

    gateway = FakeGateway()

    service = (
        factory.create_external_runtime_service(
            gateway=gateway,
        )
    )

    assert isinstance(
        service,
        ExternalRuntimeService,
    )


def test_factory_creates_runtime_application_service():
    """
    Factory should wrap ExternalRuntimeService
    inside RuntimeApplicationService.
    """

    factory = ApplicationFactory()

    runtime_service = (
        ExternalRuntimeService(
            gateway=FakeGateway(),
        )
    )

    service = (
        factory.create_runtime_application_service(
            runtime_service=runtime_service,
        )
    )

    assert isinstance(
        service,
        RuntimeApplicationService,
    )


def test_factory_rejects_missing_runtime_service():
    """
    Factory should reject invalid dependencies.
    """

    factory = ApplicationFactory()

    with pytest.raises(ValueError):

        factory.create_runtime_application_service(
            runtime_service=None,
        )