"""
EasyChatBot AI Operations Center dashboard service.

Builds the read-only Operations Center dashboard.

Architecture:

Provider Health
        |
Provider Service
        |
Provider Intelligence Service
        |
OperationsCenterDashboardService
        |
OperationsCenterDashboard
        |
Dashboard API


Responsibilities:

- compose dashboard information;
- aggregate escalation state;
- calculate operational confidence;
- create dashboard read models;
- include provider intelligence when available.

Does NOT:

- execute providers;
- modify Runtime routing;
- approve escalations;
- send notifications;
- perform remediation.
"""

from __future__ import annotations


from app.application.provider_management.escalation_history_service import (
    EscalationHistoryService,
)


from app.application.provider_management.operations_center_dashboard_models import (
    ActiveProvider,
    EscalationSummary,
    MonitoringStatus,
    MonitoringSummary,
    OperationsCenterDashboard,
    OperationsMetrics,
)


_UNSET = object()



class OperationsCenterDashboardService:
    """
    Application service responsible for dashboard composition.
    """

    def __init__(
        self,
        *,
        history_service: EscalationHistoryService,
        provider_service=None,
        provider_intelligence_service=None,
    ) -> None:

        if history_service is None:
            raise ValueError(
                "Escalation history service cannot be None."
            )


        self._history_service = (
            history_service
        )


        self._provider_service = (
            provider_service
        )


        self._provider_intelligence_service = (
            provider_intelligence_service
        )



    def build_dashboard(
        self,
        *,
        active_providers=_UNSET,
    ) -> OperationsCenterDashboard:
        """
        Build Operations Center dashboard.
        """


        #
        # Provider state
        #

        if active_providers is _UNSET:

            if self._provider_service is None:

                providers = ()

            else:

                providers = (
                    self._provider_service
                    .get_active_providers()
                )

        else:

            if active_providers is None:
                raise ValueError(
                    "Active providers cannot be None."
                )

            providers = active_providers



        #
        # Provider intelligence
        #

        provider_intelligence = ()


        if self._provider_intelligence_service is not None:

            provider_intelligence = (
                self
                ._provider_intelligence_service
                .get_all_provider_intelligence()
            )



        #
        # Escalation aggregation
        #

        pending_notifications = len(
            self._history_service
            .list_pending_notification()
        )


        pending_approvals = len(
            self._history_service
            .list_pending_approval()
        )


        approved = len(
            self._history_service
            .list_approved()
        )


        rejected = len(
            self._history_service
            .list_rejected()
        )


        total = (
            pending_notifications
            +
            pending_approvals
            +
            approved
            +
            rejected
        )


        active_escalations = (
            pending_notifications
            +
            pending_approvals
        )


        escalation_summary = EscalationSummary(
            active=active_escalations,

            pending=pending_approvals,

            pending_notifications=(
                pending_notifications
            ),

            approved=approved,

            rejected=rejected,

            total=total,
        )



        #
        # Monitoring state
        #

        if active_escalations > 0:

            monitoring = MonitoringSummary(
                status=MonitoringStatus.INCIDENT,
                message=(
                    "Operational attention required"
                ),
            )

        else:

            monitoring = MonitoringSummary(
                status=MonitoringStatus.HEALTHY,
                message=(
                    "Monitoring is healthy"
                ),
            )



        #
        # Confidence calculation
        #

        confidence = (
            100.0
            -
            (
                active_escalations
                *
                15.0
            )
        )



        return OperationsCenterDashboard(

            system_confidence=max(
                0.0,
                confidence,
            ),

            metrics=OperationsMetrics(),

            providers=tuple(
                providers
            ),

            escalations=escalation_summary,

            monitoring=monitoring,

            provider_intelligence=tuple(
                provider_intelligence
            ),
        )



#
# Backward compatibility exports
#

__all__ = [
    "ActiveProvider",
    "OperationsCenterDashboard",
    "OperationsCenterDashboardService",
]