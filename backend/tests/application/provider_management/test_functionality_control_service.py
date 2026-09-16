from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import ANY, MagicMock

import pytest

from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)


def create_service(
    *,
    authorizer: MagicMock | None = None,
    repository: MagicMock | None = None,
) -> tuple[
    FunctionalityOperationalControlService,
    MagicMock,
    MagicMock,
]:
    resolved_authorizer = (
        authorizer
        if authorizer is not None
        else MagicMock(name="authorizer")
    )

    resolved_repository = (
        repository
        if repository is not None
        else MagicMock(name="repository")
    )

    if authorizer is None:
        resolved_authorizer.can_control_functionality.return_value = True

    service = FunctionalityOperationalControlService(
        authorizer=resolved_authorizer,
        repository=resolved_repository,
    )

    return (
        service,
        resolved_authorizer,
        resolved_repository,
    )


def test_stop_disables_functionality_and_persists_transition() -> None:
    service, authorizer, repository = create_service()

    actor = object()

    repository.record_transition.return_value = MagicMock(
        functionality_id="telegram",
        environment="adults",
        availability="disabled",
        action="stop",
        reason="Maintenance",
        changed_by="admin",
    )

    result = service.stop(
        actor=actor,
        actor_name="admin",
        environment="adults",
        functionality_id="telegram",
        reason="Maintenance",
    )

    authorizer.can_control_functionality.assert_called_once_with(
        actor=actor,
        environment="adults",
        functionality_id="telegram",
    )

    repository.record_transition.assert_called_once_with(
        functionality_id="telegram",
        environment="adults",
        availability="disabled",
        action="stop",
        reason="Maintenance",
        changed_at=ANY,
        changed_by="admin",
    )

    assert result.availability == "disabled"
    assert result.action == "stop"
    assert result.reason == "Maintenance"
    assert result.changed_by == "admin"


def test_resume_enables_functionality_and_persists_transition() -> None:
    service, authorizer, repository = create_service()

    actor = object()

    repository.record_transition.return_value = MagicMock(
        functionality_id="telegram",
        environment="adults",
        availability="enabled",
        action="resume",
        reason=None,
        changed_by="admin",
    )

    result = service.resume(
        actor=actor,
        actor_name="admin",
        environment="adults",
        functionality_id="telegram",
    )

    authorizer.can_control_functionality.assert_called_once_with(
        actor=actor,
        environment="adults",
        functionality_id="telegram",
    )

    repository.record_transition.assert_called_once_with(
        functionality_id="telegram",
        environment="adults",
        availability="enabled",
        action="resume",
        reason=None,
        changed_at=ANY,
        changed_by="admin",
    )

    assert result.availability == "enabled"
    assert result.action == "resume"
    assert result.reason is None
    assert result.changed_by == "admin"


def test_stop_requires_reason() -> None:
    service, authorizer, repository = create_service()

    actor = object()

    with pytest.raises(
        ValueError,
        match="reason is required",
    ):
        service.stop(
            actor=actor,
            actor_name="admin",
            environment="adults",
            functionality_id="telegram",
            reason="",
        )

    authorizer.can_control_functionality.assert_not_called()
    repository.record_transition.assert_not_called()


def test_stop_rejects_unauthorized_actor() -> None:
    authorizer = MagicMock(name="authorizer")
    authorizer.can_control_functionality.return_value = False

    service, authorizer, repository = create_service(
        authorizer=authorizer,
    )

    actor = object()

    with pytest.raises(
        PermissionError,
        match="Not authorised to control this functionality",
    ):
        service.stop(
            actor=actor,
            actor_name="unauthorized-user",
            environment="adults",
            functionality_id="telegram",
            reason="Maintenance",
        )

    authorizer.can_control_functionality.assert_called_once_with(
        actor=actor,
        environment="adults",
        functionality_id="telegram",
    )

    repository.record_transition.assert_not_called()


def test_resume_rejects_unauthorized_actor() -> None:
    authorizer = MagicMock(name="authorizer")
    authorizer.can_control_functionality.return_value = False

    service, authorizer, repository = create_service(
        authorizer=authorizer,
    )

    actor = object()

    with pytest.raises(
        PermissionError,
        match="Not authorised to control this functionality",
    ):
        service.resume(
            actor=actor,
            actor_name="unauthorized-user",
            environment="adults",
            functionality_id="telegram",
        )

    authorizer.can_control_functionality.assert_called_once_with(
        actor=actor,
        environment="adults",
        functionality_id="telegram",
    )

    repository.record_transition.assert_not_called()


def test_invalid_environment_is_rejected() -> None:
    service, authorizer, repository = create_service()

    actor = object()

    with pytest.raises(
        ValueError,
        match="environment must be 'kids' or 'adults'",
    ):
        service.stop(
            actor=actor,
            actor_name="admin",
            environment="production",
            functionality_id="telegram",
            reason="Maintenance",
        )

    authorizer.can_control_functionality.assert_not_called()
    repository.record_transition.assert_not_called()


def test_unknown_functionality_is_rejected() -> None:
    service, authorizer, repository = create_service()

    actor = object()

    with pytest.raises(
        ValueError,
        match="Unknown functionality",
    ):
        service.stop(
            actor=actor,
            actor_name="admin",
            environment="adults",
            functionality_id="unknown_functionality",
            reason="Maintenance",
        )

    authorizer.can_control_functionality.assert_not_called()
    repository.record_transition.assert_not_called()


def test_get_availability_uses_repository_state() -> None:
    service, _, repository = create_service()

    repository.get_availability.return_value = "disabled"

    result = service.get_availability(
        environment="kids",
        functionality_id="telegram",
    )

    repository.get_availability.assert_called_once_with(
        environment="kids",
        functionality_id="telegram",
    )

    assert result == "disabled"


def test_get_last_action_uses_repository_state() -> None:
    service, _, repository = create_service()

    expected_action = MagicMock(
        functionality_id="telegram",
        environment="adults",
        availability="disabled",
        action="stop",
        reason="Maintenance",
        changed_by="admin",
        changed_at=datetime.now(timezone.utc),
    )

    repository.get_last_action.return_value = expected_action

    result = service.get_last_action(
        environment="adults",
        functionality_id="telegram",
    )

    repository.get_last_action.assert_called_once_with(
        environment="adults",
        functionality_id="telegram",
    )

    assert result is expected_action