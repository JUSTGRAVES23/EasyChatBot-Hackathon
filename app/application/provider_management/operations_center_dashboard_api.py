"""
EasyChatBot AI Operations Center dashboard API.

Provides the application-facing read-only boundary for
the Operations Center dashboard.

Architecture:

Operations Center Dashboard Service
                |
                v
      OperationsCenterDashboardFacade
                |
                v
        OperationsCenterDashboardAPI
                |
                v
          HTTP Router

Responsibilities:

- expose the dashboard application contract;
- delegate dashboard generation to the facade;
- keep HTTP concerns outside the application layer;
- preserve compatibility with explicit provider input;
- provide a stable boundary for future Operations Center
  integrations.

Does NOT:

- execute providers;
- execute agents;
- modify Runtime routing;
- access repositories directly;
- approve escalations;
- send notifications;
- perform autonomous remediation.

The dashboard is read-only.
"""

from __future__ import annotations

from typing import Any

from app.application.provider_management.operations_center_dashboard_facade import (
    OperationsCenterDashboardFacade,
)

from app.application.provider_management.operations_center_dashboard_service import (
    ActiveProvider,
)


_UNSET = object()


class OperationsCenterDashboardAPI:
    """
    Application-facing API for the Operations Center dashboard.

    The API deliberately contains no business logic.
    It delegates dashboard generation to the facade.

    For compatibility and deterministic testing, callers may
    explicitly supply active providers.

    Calling get_dashboard() without provider input preserves
    the facade's normal provider-resolution behaviour.
    """

    def __init__(
        self,
        *,
        facade: OperationsCenterDashboardFacade,
    ) -> None:
        """
        Initialise the dashboard API.
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
        active_providers: (
            tuple[
                ActiveProvider,
                ...
            ]
            | None
            | object
        ) = _UNSET,
    ) -> dict[str, Any]:
        """
        Return the current Operations Center dashboard.

        Resolution rules:

        - omitted:
            delegate to the facade without explicit provider input;

        - explicit tuple:
            delegate using the supplied providers;

        - explicit None:
            reject invalid provider input.

        The API performs no dashboard business logic.
        """

        if active_providers is None:
            raise ValueError(
                "Active providers cannot be None."
            )

        if active_providers is _UNSET:
            return self._facade.get_dashboard()

        return self._facade.get_dashboard(
            active_providers=active_providers,
        )
