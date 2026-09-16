"""
External Runtime Container.

Stores the application-configured ExternalRuntimeService.

The container:

- stores the already-composed service;
- exposes the configured service;
- supports controlled test reset.

The container does NOT:

- compose Runtime dependencies;
- create providers;
- create gateways;
- execute capabilities;
- implement governance.

Composition remains the responsibility of application bootstrap.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.external_runtime_service import (
        ExternalRuntimeService,
    )


_runtime_service: ExternalRuntimeService | None = None


def configure_external_runtime_service(
    service: ExternalRuntimeService,
) -> None:
    """
    Register the application-configured Runtime service.

    The service must already be fully composed.
    """

    global _runtime_service

    if service is None:
        raise ValueError(
            "ExternalRuntimeService cannot be None"
        )

    _runtime_service = service


def get_external_runtime_service() -> ExternalRuntimeService:
    """
    Return the configured Runtime service.

    Raises:
        RuntimeError:
            If the application has not been bootstrapped.
    """

    if _runtime_service is None:
        raise RuntimeError(
            "ExternalRuntimeService has not been configured."
        )

    return _runtime_service


def reset_runtime_container() -> None:
    """
    Reset the configured service.

    Intended for controlled test lifecycle management.
    """

    global _runtime_service

    _runtime_service = None
