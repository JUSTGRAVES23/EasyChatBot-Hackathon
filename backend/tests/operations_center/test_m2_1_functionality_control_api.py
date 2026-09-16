from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

# ---------------------------------------------------------------------------
# Repository import boundary
# ---------------------------------------------------------------------------
#
# The Hackathon repository has two legitimate Python roots:
#
#   <repo>\backend -> app.*
#   <repo>        -> src.*
#
# backend MUST take precedence for app.* while the repository root must also
# be available for legitimate app.* -> src.* dependencies.
# ---------------------------------------------------------------------------

TEST_FILE = Path(__file__).resolve()
BACKEND_ROOT = TEST_FILE.parents[2]
REPOSITORY_ROOT = BACKEND_ROOT.parent

backend_root = str(BACKEND_ROOT)
repository_root = str(REPOSITORY_ROOT)

sys.path[:] = [
    path
    for path in sys.path
    if path not in {backend_root, repository_root}
]

sys.path.insert(0, backend_root)
sys.path.insert(1, repository_root)


from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.identity import get_current_principal
from app.api.operations_center import create_operations_center_router
from app.application.operations_center.dashboard_composition import (
    OperationsCenterComposition,
)
from app.domain.identity.principal import AccountStatus, Principal


FUNCTIONALITY_ID = "voice_tts"
ENVIRONMENT = "kids"
ACTOR_NAME = "test-admin"

STOP_URL = (
    f"/api/operations-center/functionality/{FUNCTIONALITY_ID}/stop"
)

RESUME_URL = (
    f"/api/operations-center/functionality/{FUNCTIONALITY_ID}/resume"
)


def _principal() -> Principal:
    """Return a valid active principal for authorization tests."""
    return Principal(
        user_id=ACTOR_NAME,
        email="test-admin@example.test",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({"admin"}),
    )


def _operational_result(
    *,
    functionality_id: str = FUNCTIONALITY_ID,
    environment: str = ENVIRONMENT,
    availability: str = "disabled",
    action: str = "stop",
    reason: str | None = "maintenance",
    changed_by: str = ACTOR_NAME,
) -> SimpleNamespace:
    """Create the result contract consumed by the API serializer."""
    return SimpleNamespace(
        functionality_id=functionality_id,
        environment=environment,
        availability=availability,
        action=action,
        reason=reason,
        changed_at=datetime.now(timezone.utc),
        changed_by=changed_by,
    )


def _build_client(
    *,
    functionality_control_service: object | None,
) -> tuple[TestClient, object | None]:
    """
    Build the API using the real OperationsCenterComposition.

    This deliberately avoids a partial SimpleNamespace composition.

    The real composition owns the complete Operations Center dependency
    graph. The functionality-control service is the only dependency replaced
    by the test double because that is the capability under test.
    """
    composition = OperationsCenterComposition(
        functionality_control_service=functionality_control_service,
    )

    router = create_operations_center_router(
        composition=composition,
    )

    application = FastAPI()
    application.include_router(router)

    # Keep the real require_permission() dependency active.
    #
    # The identity dependency is the only authentication boundary replaced
    # here. AuthorizationService and FUNCTIONALITY_CONTROL permission
    # evaluation remain production code.
    application.dependency_overrides[get_current_principal] = _principal

    return TestClient(application), functionality_control_service


def test_stop_functionality_returns_operational_control_result() -> None:
    service = Mock(name="functionality_control_service")
    service.stop.return_value = _operational_result()

    client, control_service = _build_client(
        functionality_control_service=service,
    )

    response = client.post(
        STOP_URL,
        json={
            "environment": ENVIRONMENT,
            "reason": "maintenance",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["functionality_id"] == FUNCTIONALITY_ID
    assert body["environment"] == ENVIRONMENT
    assert body["availability"] == "disabled"
    assert body["action"] == "stop"
    assert body["reason"] == "maintenance"
    assert body["changed_by"] == ACTOR_NAME
    assert body["changed_at"]

    assert control_service is service

    service.stop.assert_called_once_with(
        actor=_principal(),
        actor_name=ACTOR_NAME,
        environment=ENVIRONMENT,
        functionality_id=FUNCTIONALITY_ID,
        reason="maintenance",
    )


def test_resume_functionality_returns_operational_control_result() -> None:
    service = Mock(name="functionality_control_service")
    service.resume.return_value = _operational_result(
        availability="enabled",
        action="resume",
        reason=None,
    )

    client, control_service = _build_client(
        functionality_control_service=service,
    )

    response = client.post(
        RESUME_URL,
        json={
            "environment": ENVIRONMENT,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["functionality_id"] == FUNCTIONALITY_ID
    assert body["environment"] == ENVIRONMENT
    assert body["availability"] == "enabled"
    assert body["action"] == "resume"
    assert body["reason"] is None
    assert body["changed_by"] == ACTOR_NAME
    assert body["changed_at"]

    assert control_service is service

    service.resume.assert_called_once_with(
        actor=_principal(),
        actor_name=ACTOR_NAME,
        environment=ENVIRONMENT,
        functionality_id=FUNCTIONALITY_ID,
    )


def test_stop_requires_reason() -> None:
    service = Mock(name="functionality_control_service")

    client, control_service = _build_client(
        functionality_control_service=service,
    )

    response = client.post(
        STOP_URL,
        json={
            "environment": ENVIRONMENT,
            "reason": "",
        },
    )

    assert response.status_code == 422
    service.stop.assert_not_called()

    assert control_service is service


def test_stop_maps_service_value_error_to_bad_request() -> None:
    service = Mock(name="functionality_control_service")
    service.stop.side_effect = ValueError(
        "A reason is required to stop a functionality."
    )

    client, control_service = _build_client(
        functionality_control_service=service,
    )

    response = client.post(
        STOP_URL,
        json={
            "environment": ENVIRONMENT,
            "reason": "maintenance",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "A reason is required to stop a functionality."
    )

    assert control_service is service

    service.stop.assert_called_once_with(
        actor=_principal(),
        actor_name=ACTOR_NAME,
        environment=ENVIRONMENT,
        functionality_id=FUNCTIONALITY_ID,
        reason="maintenance",
    )


def test_resume_maps_service_permission_error_to_forbidden() -> None:
    service = Mock(name="functionality_control_service")
    service.resume.side_effect = PermissionError(
        "Not authorised to control this functionality."
    )

    client, control_service = _build_client(
        functionality_control_service=service,
    )

    response = client.post(
        RESUME_URL,
        json={
            "environment": ENVIRONMENT,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permission."

    assert control_service is service

    service.resume.assert_called_once_with(
        actor=_principal(),
        actor_name=ACTOR_NAME,
        environment=ENVIRONMENT,
        functionality_id=FUNCTIONALITY_ID,
    )


def test_stop_maps_service_permission_error_to_forbidden() -> None:
    service = Mock(name="functionality_control_service")
    service.stop.side_effect = PermissionError(
        "Not authorised to control this functionality."
    )

    client, control_service = _build_client(
        functionality_control_service=service,
    )

    response = client.post(
        STOP_URL,
        json={
            "environment": ENVIRONMENT,
            "reason": "maintenance",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permission."

    assert control_service is service

    service.stop.assert_called_once_with(
        actor=_principal(),
        actor_name=ACTOR_NAME,
        environment=ENVIRONMENT,
        functionality_id=FUNCTIONALITY_ID,
        reason="maintenance",
    )


def test_invalid_environment_is_rejected_by_request_schema() -> None:
    service = Mock(name="functionality_control_service")

    client, control_service = _build_client(
        functionality_control_service=service,
    )

    response = client.post(
        STOP_URL,
        json={
            "environment": "invalid",
            "reason": "maintenance",
        },
    )

    # OperationsEnvironment is a Pydantic request-schema enum.
    # Invalid values therefore fail before the application service executes.
    assert response.status_code == 422

    assert control_service is service
    service.stop.assert_not_called()


def test_control_service_unavailable_returns_503() -> None:
    # None is intentional. This exercises the real endpoint guard:
    #
    # if functionality_control_service is None:
    #     raise _control_unavailable()
    client, control_service = _build_client(
        functionality_control_service=None,
    )

    response = client.post(
        STOP_URL,
        json={
            "environment": ENVIRONMENT,
            "reason": "maintenance",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Functionality operational control is not configured."
    )

    assert control_service is None


def test_resume_does_not_require_reason() -> None:
    service = Mock(name="functionality_control_service")
    service.resume.return_value = _operational_result(
        availability="enabled",
        action="resume",
        reason=None,
    )

    client, control_service = _build_client(
        functionality_control_service=service,
    )

    response = client.post(
        RESUME_URL,
        json={
            "environment": ENVIRONMENT,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["action"] == "resume"
    assert body["availability"] == "enabled"
    assert body["reason"] is None

    assert control_service is service

    service.resume.assert_called_once_with(
        actor=_principal(),
        actor_name=ACTOR_NAME,
        environment=ENVIRONMENT,
        functionality_id=FUNCTIONALITY_ID,
    )