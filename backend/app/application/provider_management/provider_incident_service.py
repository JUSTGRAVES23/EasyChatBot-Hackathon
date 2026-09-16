"""
EasyChatBot AI Operations Center provider incident service.

Tracks sustained provider availability incidents.

Architecture:

Provider Health Service
        |
        v
ProviderHealthTransitionEvent
        |
        v
ProviderIncidentService
        |
        +----------------------+
        |                      |
        v                      v
ProviderIncident       Incident Repository
        |                      |
        +----------+-----------+
                   |
                   +----------------------+
                   |                      |
                   v                      v
            Escalation Service   Operational Event Service
                                           |
                                           v
                                  Operations Center


Responsibilities:

- create provider incidents when a provider becomes
  unavailable;
- update open incidents;
- track outage start time;
- track latest observation;
- record affected capabilities;
- close incidents after recovery;
- calculate completed downtime;
- retrieve incident history;
- optionally publish operational lifecycle events.

Does NOT:

- execute providers;
- perform health probes;
- modify Runtime routing;
- send emails;
- approve recommendations;
- perform autonomous failover.

Incident persistence is kept behind a repository boundary.
The current implementation uses an in-memory repository
for Hackathon validation.

Operational event publication is optional so that existing
incident-service callers remain backwards compatible.
"""

from __future__ import annotations

from uuid import uuid4

from app.application.provider_management.operational_event_service import (
    OperationalEventService,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthStatus,
    ProviderHealthTransition,
    ProviderHealthTransitionEvent,
    ProviderIncident,
)


class ProviderIncidentRepository:
    """
    Minimal persistence contract for provider incidents.

    A database-backed implementation can replace the
    in-memory implementation without changing the service.
    """

    def save(
        self,
        incident: ProviderIncident,
    ) -> None:
        """
        Persist an incident.
        """

        raise NotImplementedError

    def get_open(
        self,
        provider: str,
    ) -> ProviderIncident | None:
        """
        Retrieve the currently open incident for a provider.
        """

        raise NotImplementedError

    def get_all(
        self,
    ) -> list[ProviderIncident]:
        """
        Retrieve incident history.
        """

        raise NotImplementedError


class InMemoryProviderIncidentRepository(
    ProviderIncidentRepository,
):
    """
    In-memory incident repository.

    Intended for:

    - development;
    - testing;
    - Hackathon validation.

    It can later be replaced with SQLite or PostgreSQL.
    """

    def __init__(self) -> None:
        self._incidents: list[
            ProviderIncident
        ] = []

    def save(
        self,
        incident: ProviderIncident,
    ) -> None:
        """
        Save an incident.

        If the incident already exists, replace it.
        """

        if incident is None:
            raise ValueError(
                "Provider incident cannot be None."
            )

        for index, existing in enumerate(
            self._incidents
        ):
            if (
                existing.incident_id
                == incident.incident_id
            ):
                self._incidents[index] = incident
                return

        self._incidents.append(
            incident
        )

    def get_open(
        self,
        provider: str,
    ) -> ProviderIncident | None:
        """
        Return the open incident for a provider.
        """

        for incident in reversed(
            self._incidents
        ):
            if (
                incident.provider == provider
                and incident.is_open
            ):
                return incident

        return None

    def get_all(
        self,
    ) -> list[ProviderIncident]:
        """
        Return incident history as a copy.
        """

        return list(
            self._incidents
        )


class ProviderIncidentService:
    """
    Application service responsible for provider
    availability incident lifecycle.

    Lifecycle:

        HEALTHY
           |
           v
        DEGRADED
           |
           v
        UNAVAILABLE
           |
           v
        OPEN INCIDENT
           |
           v
        RECOVERED
           |
           v
        CLOSED INCIDENT

    Operational events:

        New unavailable incident
                |
                v
        PROVIDER_INCIDENT_CREATED

        Recovered open incident
                |
                v
        PROVIDER_RECOVERED
    """

    def __init__(
        self,
        repository: ProviderIncidentRepository,
        operational_event_service: (
            OperationalEventService | None
        ) = None,
    ) -> None:
        """
        Initialise the incident service.

        The operational event service is optional to preserve
        backwards compatibility with existing callers and tests.
        """

        if repository is None:
            raise ValueError(
                "Provider incident repository "
                "cannot be None."
            )

        self._repository = repository

        self._operational_event_service = (
            operational_event_service
        )

    def process_transition(
        self,
        event: ProviderHealthTransitionEvent,
    ) -> ProviderIncident | None:
        """
        Process a provider health transition.

        Returns:

        - the newly created incident;
        - the updated incident;
        - the recovered incident;

        or None when no incident lifecycle action
        is required.

        The service does not send notifications or
        trigger provider changes.
        """

        if event is None:
            raise ValueError(
                "Provider health transition "
                "cannot be None."
            )

        if not event.provider.strip():
            raise ValueError(
                "Provider cannot be empty."
            )

        if (
            event.transition
            == ProviderHealthTransition.UNAVAILABLE
        ):
            return self._handle_unavailable(
                event
            )

        if (
            event.transition
            == ProviderHealthTransition.RECOVERED
        ):
            return self._handle_recovery(
                event
            )

        if (
            event.transition
            == ProviderHealthTransition.DEGRADED
        ):
            return self._handle_degraded(
                event
            )

        return None

    def list_incidents(
        self,
    ) -> list[ProviderIncident]:
        """
        Return provider incident history.
        """

        return self._repository.get_all()

    def get_open_incident(
        self,
        provider: str,
    ) -> ProviderIncident | None:
        """
        Return the currently open incident for a provider.
        """

        if not provider.strip():
            raise ValueError(
                "Provider cannot be empty."
            )

        return self._repository.get_open(
            provider
        )

    def _handle_unavailable(
        self,
        event: ProviderHealthTransitionEvent,
    ) -> ProviderIncident:
        """
        Create or update an unavailable-provider incident.

        A new incident emits PROVIDER_INCIDENT_CREATED.

        Repeated unavailable observations update the existing
        incident but do not create duplicate lifecycle events.
        """

        existing = (
            self._repository.get_open(
                event.provider
            )
        )

        if existing is not None:
            updated = ProviderIncident(
                incident_id=existing.incident_id,
                provider=existing.provider,
                status=(
                    ProviderHealthStatus.UNAVAILABLE
                ),
                started_at=existing.started_at,
                last_observed_at=(
                    event.occurred_at
                ),
                recovered_at=None,
                affected_capabilities=(
                    self._merge_capabilities(
                        existing.affected_capabilities,
                        event.affected_capabilities,
                    )
                ),
                consecutive_failures=(
                    event.consecutive_failures
                ),
                resolution_message=None,
            )

            self._repository.save(
                updated
            )

            return updated

        incident = ProviderIncident(
            incident_id=str(uuid4()),
            provider=event.provider,
            status=(
                ProviderHealthStatus.UNAVAILABLE
            ),
            started_at=event.occurred_at,
            last_observed_at=event.occurred_at,
            recovered_at=None,
            affected_capabilities=(
                tuple(
                    sorted(
                        set(
                            event.affected_capabilities
                        )
                    )
                )
            ),
            consecutive_failures=(
                event.consecutive_failures
            ),
            resolution_message=None,
        )

        self._repository.save(
            incident
        )

        self._publish_incident_created(
            incident
        )

        return incident

    def _handle_recovery(
        self,
        event: ProviderHealthTransitionEvent,
    ) -> ProviderIncident | None:
        """
        Close the provider's open incident after recovery.

        A successfully closed incident emits
        PROVIDER_RECOVERED.
        """

        existing = (
            self._repository.get_open(
                event.provider
            )
        )

        if existing is None:
            return None

        recovered = ProviderIncident(
            incident_id=existing.incident_id,
            provider=existing.provider,
            status=ProviderHealthStatus.HEALTHY,
            started_at=existing.started_at,
            last_observed_at=event.occurred_at,
            recovered_at=event.occurred_at,
            affected_capabilities=(
                self._merge_capabilities(
                    existing.affected_capabilities,
                    event.affected_capabilities,
                )
            ),
            consecutive_failures=(
                existing.consecutive_failures
            ),
            resolution_message=(
                "Provider recovered after "
                "successful health observations."
            ),
        )

        self._repository.save(
            recovered
        )

        self._publish_provider_recovered(
            recovered
        )

        return recovered

    def _handle_degraded(
        self,
        event: ProviderHealthTransitionEvent,
    ) -> ProviderIncident | None:
        """
        Update an existing incident if the provider
        is already under an open incident.

        A single degraded observation does not create
        a provider outage incident.
        """

        existing = (
            self._repository.get_open(
                event.provider
            )
        )

        if existing is None:
            return None

        updated = ProviderIncident(
            incident_id=existing.incident_id,
            provider=existing.provider,
            status=existing.status,
            started_at=existing.started_at,
            last_observed_at=event.occurred_at,
            recovered_at=None,
            affected_capabilities=(
                self._merge_capabilities(
                    existing.affected_capabilities,
                    event.affected_capabilities,
                )
            ),
            consecutive_failures=(
                event.consecutive_failures
            ),
            resolution_message=None,
        )

        self._repository.save(
            updated
        )

        return updated

    def _publish_incident_created(
        self,
        incident: ProviderIncident,
    ) -> None:
        """
        Publish a provider incident-created operational event
        when the integration service is configured.
        """

        if (
            self._operational_event_service
            is None
        ):
            return

        event = (
            self._operational_event_service
            .record_incident_created(
                incident=incident,
            )
        )

        if event is None:
            raise RuntimeError(
                "Provider incident operational "
                "event service returned no event."
            )

    def _publish_provider_recovered(
        self,
        incident: ProviderIncident,
    ) -> None:
        """
        Publish a provider recovery operational event
        when the integration service is configured.
        """

        if (
            self._operational_event_service
            is None
        ):
            return

        event = (
            self._operational_event_service
            .record_provider_recovered(
                incident=incident,
            )
        )

        if event is None:
            raise RuntimeError(
                "Provider recovery operational "
                "event service returned no event."
            )

    @staticmethod
    def _merge_capabilities(
        existing: tuple[str, ...],
        incoming: tuple[str, ...],
    ) -> tuple[str, ...]:
        """
        Merge affected capabilities without duplicates.
        """

        return tuple(
            sorted(
                set(existing)
                | set(incoming)
            )
        )