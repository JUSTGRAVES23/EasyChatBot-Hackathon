from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import api.routes as routes
from app.domain.identity.principal import AccountStatus, Principal


@dataclass
class CapturedService:
    request: object | None = None

    async def execute(self, *, capability: str, payload: dict, actor=None):
        self.request = SimpleNamespace(
            capability=capability,
            payload=payload,
            actor=actor,
        )
        return {
            "request_id": "test-request",
            "capability": capability,
            "status": "completed",
            "output": {"ok": True},
        }


@pytest.mark.asyncio
async def test_runtime_route_propagates_authenticated_principal_as_actor(
    monkeypatch,
) -> None:
    service = CapturedService()
    principal = Principal(
        user_id="operator-1",
        email="operator@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({"operator"}),
    )

    monkeypatch.setattr(
        routes,
        "create_runtime_application_service",
        lambda: service,
    )

    payload = SimpleNamespace(
        capability="internal_data_read",
        payload={"user_id": "target-user"},
    )

    result = await routes.execute_runtime(
        payload,
        principal=principal,
    )

    assert result.request_id == "test-request"
    assert service.request is not None
    assert service.request.actor.actor_id == "operator-1"
    assert service.request.actor.roles == frozenset({"operator"})


@pytest.mark.asyncio
async def test_runtime_route_does_not_create_actor_from_payload(
    monkeypatch,
) -> None:
    service = CapturedService()
    principal = Principal(
        user_id="operator-1",
        email="operator@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({"operator"}),
    )

    monkeypatch.setattr(
        routes,
        "create_runtime_application_service",
        lambda: service,
    )

    payload = SimpleNamespace(
        capability="internal_data_read",
        payload={
            "user_id": "target-user",
            "actor_id": "spoofed",
            "roles": ["admin"],
        },
    )

    await routes.execute_runtime(
        payload,
        principal=principal,
    )

    assert service.request.actor.actor_id == "operator-1"
    assert service.request.actor.roles == frozenset({"operator"})

