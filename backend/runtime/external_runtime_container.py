"""
External Runtime Container.

Owns the configured ExternalRuntimeService instance.

Responsibilities:

- store configured runtime service;
- provide runtime dependency access;
- reset runtime state for controlled tests.

Does NOT:

- create providers;
- create executors;
- build gateways;
- execute capabilities;
- implement governance.

Composition belongs to:

    backend.application.bootstrap

"""

from __future__ import annotations

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)


_runtime_service: ExternalRuntimeService | None = None


def configure_external_runtime_service(
    service: ExternalRuntimeService,
) -> None:
    """
    Register configured ExternalRuntimeService.

    Called by application bootstrap.

    The container only stores the already-created
    service instance.

    It does not perform composition.

    Args:
        service:
            Configured ExternalRuntimeService.

    Raises:
        ValueError:
            If service is None.
    """

    global _runtime_service

    if service is None:
        raise ValueError(
            "ExternalRuntimeService cannot be None."
        )

    _runtime_service = service


def get_external_runtime_service() -> ExternalRuntimeService:
    """
    Retrieve configured ExternalRuntimeService.

    Used by application boundaries requiring
    Runtime capability execution.

    Raises:
        RuntimeError:
            If bootstrap has not completed.
    """

    if _runtime_service is None:
        raise RuntimeError(
            "ExternalRuntimeService has not been configured."
        )

    return _runtime_service


def reset_runtime_container() -> None:
    """
    Reset configured ExternalRuntimeService.

    Test utility only.

    Production lifecycle:

        bootstrap
            |
            v
        configure service

    This function does not:

    - create Runtime services;
    - create providers;
    - create gateways;
    - execute capabilities.
    """

    global _runtime_service

    _runtime_service = None