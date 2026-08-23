import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.governance.api.governance_audit_api import (
    get_governance_audit_service,
    router,
)
from backend.governance.governance_audit_service import (
    GovernanceAuditService,
)


@pytest.mark.asyncio
async def test_governance_audit_api_returns_recorded_events():

    audit_service = GovernanceAuditService()

    audit_service.record(
        event="PROVIDER_PAUSED",
        actor="admin",
        reason="Provider incident",
        component="provider_management",
    )

    application = FastAPI()
    application.include_router(router)

    application.dependency_overrides[
        get_governance_audit_service
    ] = lambda: audit_service

    transport = ASGITransport(
        app=application,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/governance/audit/events"
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["count"] == 1
    assert len(payload["events"]) == 1

    event = payload["events"][0]

    assert event["event"] == "PROVIDER_PAUSED"
    assert event["actor"] == "admin"
    assert event["reason"] == "Provider incident"
    assert event["component"] == "provider_management"
    assert event["timestamp"]


@pytest.mark.asyncio
async def test_governance_audit_api_returns_empty_store():

    audit_service = GovernanceAuditService()

    application = FastAPI()
    application.include_router(router)

    application.dependency_overrides[
        get_governance_audit_service
    ] = lambda: audit_service

    transport = ASGITransport(
        app=application,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/governance/audit/events"
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["events"] == []
    assert payload["count"] == 0


@pytest.mark.asyncio
async def test_governance_audit_api_is_read_only():

    audit_service = GovernanceAuditService()

    audit_service.record(
        event="CYBERSECURITY_DELIVERY_PAUSED",
        actor="admin",
        reason="Security incident",
        component="cybersecurity_delivery",
    )

    application = FastAPI()
    application.include_router(router)

    application.dependency_overrides[
        get_governance_audit_service
    ] = lambda: audit_service

    transport = ASGITransport(
        app=application,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/governance/audit/events"
        )

    assert response.status_code == 200
    assert audit_service.list_events()[0].event == (
        "CYBERSECURITY_DELIVERY_PAUSED"
    )
