"""
EasyChatBot AI Operations Center dashboard facade.

Provides a stable application-facing contract for the
Operations Center presentation/API layer.

Architecture:

Provider Health
      |
Escalations
      |
Workflow
      |
History Service
      |
Dashboard Service
      |
      v
OperationsCenterDashboardFacade
      |
      +----------------------+
      |                      |
      v                      v
Provider Mapper       Dashboard Contract
      |
      v
API / Frontend


Responsibilities:

- expose dashboard information to presentation layers;
- convert dashboard read models into stable API output;
- keep frontend/API independent from application internals;
- preserve compatibility with existing consumers.

Does NOT:

- execute providers;
- calculate intelligence;
- query repositories;
- change Runtime routing;
- approve escalations;
- reject escalations;
- send notifications;
- perform autonomous operational actions.

This is a read-only presentation boundary.
"""

from __future__ import annotations


from typing import Any


from app.application.provider_management.operations_center_dashboard_service import (
    ActiveProvider,
    OperationsCenterDashboard,
    OperationsCenterDashboardService,
)


from app.application.provider_management.operations_center_provider_intelligence_dashboard_mapper import (
    OperationsCenterProviderIntelligenceDashboardMapper,
)



_UNSET = object()



class OperationsCenterDashboardFacade:
    """
    Presentation-facing facade for the AI Operations Center.
    """


    def __init__(
        self,
        dashboard_service: OperationsCenterDashboardService,
    ) -> None:
        """
        Initialise the dashboard facade.
        """

        if dashboard_service is None:
            raise ValueError(
                "Operations Center dashboard service "
                "cannot be None."
            )


        self._dashboard_service = (
            dashboard_service
        )



    def get_dashboard(
        self,
        *,
        active_providers=(
            _UNSET
        ),
    ) -> dict[str, Any]:
        """
        Return a frontend-safe dashboard representation.
        """

        if active_providers is None:
            raise ValueError(
                "Active providers cannot be None."
            )


        if active_providers is _UNSET:

            dashboard = (
                self._dashboard_service
                .build_dashboard()
            )

        else:

            dashboard = (
                self._dashboard_service
                .build_dashboard(
                    active_providers=(
                        active_providers
                    )
                )
            )


        return self._serialize_dashboard(
            dashboard
        )



    @staticmethod
    def _serialize_dashboard(
        dashboard: OperationsCenterDashboard,
    ) -> dict[str, Any]:
        """
        Convert dashboard read model into
        stable API contract.
        """

        return {

            "system_confidence": (
                dashboard.system_confidence
            ),


            "monitoring_status": (
                dashboard.monitoring_status.value
            ),


            "active_providers": [

                OperationsCenterDashboardFacade
                ._serialize_provider(
                    provider
                )

                for provider

                in dashboard.active_providers
            ],


            "provider_intelligence": (

                OperationsCenterProviderIntelligenceDashboardMapper
                .to_dashboard_list(
                    dashboard.provider_intelligence
                )

            ),


            "active_escalations": (
                dashboard.active_escalations
            ),


            "pending_approvals": (
                dashboard.pending_approvals
            ),


            "approved_escalations": (
                dashboard.approved_escalations
            ),


            "rejected_escalations": (
                dashboard.rejected_escalations
            ),


            "pending_notifications": (
                dashboard.pending_notifications
            ),


            "total_escalations": (
                dashboard.total_escalations
            ),
        }



    @staticmethod
    def _serialize_provider(
        provider: ActiveProvider,
    ) -> dict[str, Any]:
        """
        Convert provider into existing frontend contract.

        Intentionally minimal to preserve
        backward compatibility.
        """

        return {

            "provider": (
                provider.provider
            ),

            "model": (
                provider.model
            ),

            "capabilities": list(
                provider.capabilities
            ),

            "active": (
                provider.active
            ),
        }



__all__ = [
    "OperationsCenterDashboardFacade",
]