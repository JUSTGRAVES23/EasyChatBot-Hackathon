"""
EasyChatBot AI Operations Center provider service.

Bridges provider health state into the Operations
Center dashboard provider read model.

Architecture:

Provider Health Monitor
        |
        v
ProviderHealthReadModel
        |
        v
OperationsCenterProviderService
        |
        v
ActiveProvider
        |
        v
Operations Center Dashboard


Responsibilities:

- expose dashboard-safe provider information;
- translate health state into UI fields;
- preserve provider health separation.

Does NOT:

- execute providers;
- perform health probes;
- change Runtime routing;
- perform remediation.
"""

from __future__ import annotations


from app.application.provider_management.operations_center_dashboard_models import (
    ActiveProvider,
)

from app.application.provider_management.provider_health_monitor_service import (
    ProviderHealthMonitorService,
)


class OperationsCenterProviderService:
    """
    Provides provider information for Operations Center.
    """


    def __init__(
        self,
        *,
        health_monitor: ProviderHealthMonitorService,
    ) -> None:

        if health_monitor is None:
            raise ValueError(
                "Provider health monitor cannot be None."
            )

        self._health_monitor = health_monitor


    def get_active_providers(
        self,
    ) -> tuple[ActiveProvider, ...]:
        """
        Return dashboard provider information.

        Consumes ProviderHealthReadModel only.
        """

        health_records = (
            self._health_monitor
            .get_all_provider_health()
        )


        providers: list[ActiveProvider] = []


        for record in health_records:

            if record.model is None:
                continue


            capabilities = ()

            if record.capability:
                capabilities = (
                    record.capability,
                )


            status_value = (
                record.status.value
                if hasattr(
                    record.status,
                    "value",
                )
                else str(
                    record.status
                )
            )


            providers.append(
                ActiveProvider(
                    provider=record.provider,

                    model=record.model,

                    capabilities=capabilities,

                    active=(
                        status_value
                        != "unavailable"
                    ),

                    health_status=status_value,

                    # ProviderHealthReadModel does not
                    # expose latency or counters.
                    # Keep dashboard contract safe.
                    latency_ms=None,

                    consecutive_failures=0,

                    consecutive_successes=0,

                    current_incident=(
                        status_value
                        == "unavailable"
                    ),
                )
            )


        return tuple(providers)


__all__ = [
    "OperationsCenterProviderService",
]