"""
EasyChatBot AI Operations Center dashboard contract tests.

Validates the stable dashboard API contract.

The frontend (desktop and mobile/iPhone)
depends on this contract.

This test intentionally does NOT validate:
- UI rendering;
- CSS;
- responsive behaviour.

Those belong to the frontend layer.

It validates:
- required dashboard fields exist;
- response types remain stable;
- provider intelligence contract exists;
- dashboard remains read-only.
"""

from __future__ import annotations


from app.application.provider_management.operations_center_dashboard_composition import (
    create_operations_center_composition,
)


EXPECTED_FIELDS = {
    "system_confidence",
    "monitoring_status",
    "active_providers",
    "provider_intelligence",
    "active_escalations",
    "pending_approvals",
    "approved_escalations",
    "rejected_escalations",
    "pending_notifications",
    "total_escalations",
}


def test_operations_center_dashboard_contract_fields() -> None:
    """
    Validate stable dashboard response fields.
    """

    composition = (
        create_operations_center_composition()
    )

    dashboard = (
        composition
        .dashboard_api
        .get_dashboard()
    )


    assert isinstance(
        dashboard,
        dict,
    )


    assert EXPECTED_FIELDS.issubset(
        dashboard.keys()
    )



def test_operations_center_dashboard_contract_types() -> None:
    """
    Validate dashboard field types consumed by frontend.
    """

    composition = (
        create_operations_center_composition()
    )

    dashboard = (
        composition
        .dashboard_api
        .get_dashboard()
    )


    assert isinstance(
        dashboard["system_confidence"],
        float,
    )


    assert isinstance(
        dashboard["monitoring_status"],
        str,
    )


    assert isinstance(
        dashboard["active_providers"],
        list,
    )


    assert isinstance(
        dashboard["provider_intelligence"],
        list,
    )


    assert isinstance(
        dashboard["active_escalations"],
        int,
    )


    assert isinstance(
        dashboard["pending_approvals"],
        int,
    )


    assert isinstance(
        dashboard["approved_escalations"],
        int,
    )


    assert isinstance(
        dashboard["rejected_escalations"],
        int,
    )


    assert isinstance(
        dashboard["pending_notifications"],
        int,
    )


    assert isinstance(
        dashboard["total_escalations"],
        int,
    )



def test_provider_contract_when_provider_exists() -> None:
    """
    Validate provider object contract.

    The dashboard must remain compatible with
    desktop and mobile frontend cards.
    """

    composition = (
        create_operations_center_composition()
    )


    composition.health_application_service.observe(
        _create_observation()
    )


    dashboard = (
        composition
        .dashboard_api
        .get_dashboard()
    )


    providers = (
        dashboard["active_providers"]
    )


    assert len(
        providers
    ) == 1


    provider = providers[0]


    assert {
        "provider",
        "model",
        "capabilities",
        "active",
    }.issubset(
        provider.keys()
    )


def _create_observation():
    """
    Create deterministic provider health data.
    """

    from datetime import (
        datetime,
        timezone,
    )

    from app.application.provider_management.provider_health_models import (
        ProviderHealthObservation,
        ProviderHealthStatus,
    )


    return ProviderHealthObservation(
        provider="ollama",
        model="gpt-oss:120b",
        capability="cloud_llm",
        status=ProviderHealthStatus.HEALTHY,
        observed_at=datetime(
            2026,
            8,
            17,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        latency_ms=120,
    )