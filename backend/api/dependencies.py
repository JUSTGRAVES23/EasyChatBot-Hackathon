"""
EasyChatBot API Dependencies.

FastAPI dependency providers.

Responsibilities:

- expose configured application services;
- retrieve Runtime services;
- provide dependency injection boundaries.

This module does not:

- create providers;
- create agents;
- create executors;
- build Runtime gateways;
- execute capabilities.

Composition belongs to:

backend.application.bootstrap
"""

from __future__ import annotations


from services.external_runtime_service import (
    ExternalRuntimeService,
)

from runtime.external_runtime_container import (
    get_external_runtime_service,
)



def get_runtime_service() -> ExternalRuntimeService:
    """
    FastAPI dependency.

    Returns the configured ExternalRuntimeService.

    The service must have been configured during
    application bootstrap.

    Raises:
        RuntimeError:
            If bootstrap has not completed.
    """

    return get_external_runtime_service()
