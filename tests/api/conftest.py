"""
API test composition fixtures.

Provides controlled application dependencies
for API tests.

Tests must not:

- create real providers;
- call external services;
- execute real Runtime infrastructure.

Instead they inject approved test doubles.
"""

from __future__ import annotations

import pytest

from unittest.mock import AsyncMock, Mock

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)

from backend.api.routes import (
    configure_external_runtime_service,
)


@pytest.fixture
def mock_external_runtime_service():
    """
    Create a controlled ExternalRuntimeService
    for API tests.
    """

    gateway = Mock(
        spec=CapabilityGateway,
    )

    service = ExternalRuntimeService(
        gateway=gateway,
    )

    service.execute = AsyncMock()

    configure_external_runtime_service(
        service,
    )

    return service