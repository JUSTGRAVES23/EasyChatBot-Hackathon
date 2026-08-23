"""
EasyChatBot AI Operations Center dashboard API adapter.

Provides a thin presentation/API boundary over the
Operations Center dashboard facade.

Architecture:

Provider Management Application
        |
        v
OperationsCenterDashboardFacade
        |
        v
OperationsCenterDashboardAPI
        |
        v
HTTP / Frontend


Responsibilities:

- expose the dashboard through a stable API-facing contract;
- validate API inputs;
- delegate dashboard generation to the application facade;
- return JSON-safe data.

Does NOT:

- access repositories directly;
- execute providers;
- modify Runtime routing;
- approve escalations;
- reject escalations;
- send emails;
- perform autonomous operational actions.

Business logic remains in the application layer.
"""

from __future__ import annotations

from typing import Any

from app.application.provider_management.operations_center_dashboard_facade import (
    OperationsCenterDashboardFacade,
)

from app.application.provider_management.operations_center_dashboard_service import (
    ActiveProvider,
)


class OperationsCenterDashboardAPI:
    """
    Thin API adapter for the Operations Center dashboard.

    This class deliberately contains no provider-management
    business rules.
    """

    def __init__(
        self,
        facade: OperationsCenterDashboardFacade,
    ) -> None:
        """
        Initialise the API adapter.
        """

        if facade is None:
            raise ValueError(
                "Operations Center dashboard facade "
                "cannot be None."
            )

        self._facade = facade

    def get_dashboard(
        self,
        *,
        active_providers: tuple[
            ActiveProvider,
            ...
        ],
    ) -> dict[str, Any]:
        """
        Return the Operations Center dashboard.

        The API adapter delegates completely to the
        application facade.
        """

        if active_providers is None:
            raise ValueError(
                "Active providers cannot be None."
            )

        return self._facade.get_dashboard(
            active_providers=active_providers,
        )