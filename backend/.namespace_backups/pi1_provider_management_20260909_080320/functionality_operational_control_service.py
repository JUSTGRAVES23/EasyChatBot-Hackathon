from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Protocol

from app.application.provider_management.functionality_registry import (
    is_known_functionality,
)


class FunctionalityControlAuthorizer(Protocol):
    def can_control_functionality(
        self, *, actor: object, environment: str, functionality_id: str
    ) -> bool: ...


class FunctionalityControlAuditor(Protocol):
    def record_functionality_control(
        self,
        *,
        actor: object,
        environment: str,
        functionality_id: str,
        action: str,
        reason: str | None,
        changed_at: datetime,
    ) -> None: ...


@dataclass(frozen=True)
class OperationalControlResult:
    functionality_id: str
    environment: str
    availability: str
    action: str
    reason: str | None
    changed_at: datetime
    changed_by: str


class FunctionalityControlRepository(Protocol):
    def get_availability(
        self, *, environment: str, functionality_id: str
    ) -> str: ...

    def get_last_action(
        self, *, environment: str, functionality_id: str
    ) -> OperationalControlResult | None: ...

    def record_transition(
        self,
        *,
        functionality_id: str,
        environment: str,
        availability: str,
        action: str,
        reason: str | None,
        changed_at: datetime,
        changed_by: str,
    ) -> OperationalControlResult: ...


class FunctionalityOperationalControlService:
    VALID_ENVIRONMENTS = {"kids", "adults"}

    def __init__(
        self,
        *,
        authorizer: FunctionalityControlAuthorizer,
        auditor: FunctionalityControlAuditor | None = None,
        repository: FunctionalityControlRepository | None = None,
    ) -> None:
        if auditor is None and repository is None:
            raise ValueError("auditor or repository is required.")

        self._authorizer = authorizer
        self._auditor = auditor
        self._repository = repository
        self._lock = RLock()

        # Compatibility fallback for existing unit-test/in-memory usage.
        self._availability: dict[tuple[str, str], str] = {}
        self._last_action: dict[
            tuple[str, str], OperationalControlResult
        ] = {}

    def stop(
        self,
        *,
        actor: object,
        actor_name: str,
        environment: str,
        functionality_id: str,
        reason: str,
    ) -> OperationalControlResult:
        self._validate(environment, functionality_id)

        clean_reason = reason.strip()
        if not clean_reason:
            raise ValueError("A reason is required to stop a functionality.")

        self._authorize(actor, environment, functionality_id)

        return self._transition(
            actor=actor,
            actor_name=actor_name,
            environment=environment,
            functionality_id=functionality_id,
            action="stop",
            availability="disabled",
            reason=clean_reason,
        )

    def resume(
        self,
        *,
        actor: object,
        actor_name: str,
        environment: str,
        functionality_id: str,
    ) -> OperationalControlResult:
        self._validate(environment, functionality_id)
        self._authorize(actor, environment, functionality_id)

        return self._transition(
            actor=actor,
            actor_name=actor_name,
            environment=environment,
            functionality_id=functionality_id,
            action="resume",
            availability="enabled",
            reason=None,
        )

    def get_availability(
        self,
        *,
        environment: str,
        functionality_id: str,
    ) -> str:
        self._validate(environment, functionality_id)

        if self._repository is not None:
            return self._repository.get_availability(
                environment=environment,
                functionality_id=functionality_id,
            )

        with self._lock:
            return self._availability.get(
                (environment, functionality_id),
                "enabled",
            )

    def get_last_action(
        self,
        *,
        environment: str,
        functionality_id: str,
    ) -> OperationalControlResult | None:
        self._validate(environment, functionality_id)

        if self._repository is not None:
            return self._repository.get_last_action(
                environment=environment,
                functionality_id=functionality_id,
            )

        with self._lock:
            return self._last_action.get(
                (environment, functionality_id)
            )

    def _authorize(
        self,
        actor: object,
        environment: str,
        functionality_id: str,
    ) -> None:
        if not self._authorizer.can_control_functionality(
            actor=actor,
            environment=environment,
            functionality_id=functionality_id,
        ):
            raise PermissionError(
                "Not authorised to control this functionality."
            )

    def _transition(
        self,
        *,
        actor: object,
        actor_name: str,
        environment: str,
        functionality_id: str,
        action: str,
        availability: str,
        reason: str | None,
    ) -> OperationalControlResult:
        changed_at = datetime.now(timezone.utc)

        if self._repository is not None:
            return self._repository.record_transition(
                functionality_id=functionality_id,
                environment=environment,
                availability=availability,
                action=action,
                reason=reason,
                changed_at=changed_at,
                changed_by=actor_name,
            )

        result = OperationalControlResult(
            functionality_id=functionality_id,
            environment=environment,
            availability=availability,
            action=action,
            reason=reason,
            changed_at=changed_at,
            changed_by=actor_name,
        )

        with self._lock:
            self._availability[
                (environment, functionality_id)
            ] = availability
            self._last_action[
                (environment, functionality_id)
            ] = result

        if self._auditor is None:
            raise RuntimeError(
                "Control auditor is required for in-memory operation."
            )

        self._auditor.record_functionality_control(
            actor=actor,
            environment=environment,
            functionality_id=functionality_id,
            action=action,
            reason=reason,
            changed_at=changed_at,
        )

        return result

    @classmethod
    def _validate(
        cls,
        environment: str,
        functionality_id: str,
    ) -> None:
        if environment not in cls.VALID_ENVIRONMENTS:
            raise ValueError("environment must be 'kids' or 'adults'")

        if not functionality_id.strip():
            raise ValueError("functionality_id is required")

        if not is_known_functionality(functionality_id):
            raise ValueError(
                f"Unknown functionality_id: {functionality_id}"
            )


