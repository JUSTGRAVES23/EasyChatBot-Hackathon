from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from backend.app.application.privacy.privacy_change_registry import (
    PrivacyChangeRegistry,
)
from backend.app.application.privacy.privacy_governance_case import (
    PrivacyGovernanceCase,
    PrivacyTriggerType,
)
from backend.app.application.privacy.privacy_governance_case_change_link import (
    PrivacyGovernanceCaseChangeLinkService,
)
from backend.app.application.privacy.privacy_governance_case_registry import (
    PrivacyGovernanceCaseRegistry,
)


def make_change() -> PrivacyChange:
    return PrivacyChange(
        change_id="PCR-LINK-001",
        title="New learner processing",
        description="Controlled processing change.",
        risk=PrivacyChangeRisk.HIGH,
        status=PrivacyChangeStatus.PENDING_DPO_GRC,
        dpo_required=True,
        grc_required=True,
    )


def make_case(
    *,
    change_id: str | None = "PCR-LINK-001",
) -> PrivacyGovernanceCase:
    return PrivacyGovernanceCase(
        case_id="CASE-LINK-001",
        title="New learner processing",
        summary="Controlled processing change.",
        trigger_type=PrivacyTriggerType.NEW_PROCESSING,
        triggered_at=datetime.now(timezone.utc),
        trigger_source="Processing Registry",
        change_id=change_id,
        risk="HIGH",
        validation_status="PASS",
        governance_status="PENDING_DPO_GRC",
    )


def make_service(
    case: PrivacyGovernanceCase | None = None,
):
    cases = PrivacyGovernanceCaseRegistry()

    cases.register(
        case or make_case()
    )

    changes = PrivacyChangeRegistry()

    changes.register(
        make_change()
    )

    return PrivacyGovernanceCaseChangeLinkService(
        case_registry=cases,
        change_registry=changes,
    )


def test_case_resolves_to_authoritative_change():
    service = make_service()

    link = service.get_link(
        "CASE-LINK-001"
    )

    assert link.case.case_id == "CASE-LINK-001"

    assert (
        link.case.change_id
        == "PCR-LINK-001"
    )

    assert (
        link.change.change_id
        == "PCR-LINK-001"
    )

    assert (
        link.change.title
        == "New learner processing"
    )

    assert (
        link.change.risk
        == PrivacyChangeRisk.HIGH
    )

    assert (
        link.change.status
        == PrivacyChangeStatus.PENDING_DPO_GRC
    )


def test_get_change_for_case_returns_registry_object():
    service = make_service()

    change = service.get_change_for_case(
        "CASE-LINK-001"
    )

    assert (
        change.change_id
        == "PCR-LINK-001"
    )


def test_missing_change_relationship_is_controlled():
    service = make_service(
        make_case(change_id=None)
    )

    with pytest.raises(
        ValueError,
        match="no change_id relationship",
    ):
        service.get_link(
            "CASE-LINK-001"
        )


def test_missing_change_is_controlled():
    cases = PrivacyGovernanceCaseRegistry()

    cases.register(
        make_case()
    )

    changes = PrivacyChangeRegistry()

    service = PrivacyGovernanceCaseChangeLinkService(
        case_registry=cases,
        change_registry=changes,
    )

    with pytest.raises(
        KeyError,
        match="Privacy change not found",
    ):
        service.get_link(
            "CASE-LINK-001"
        )


def test_list_links_preserves_one_to_one_case_change_traceability():
    service = make_service()

    links = service.list_links()

    assert len(links) == 1

    assert (
        links[0].case.case_id
        == "CASE-LINK-001"
    )

    assert (
        links[0].case.change_id
        == "PCR-LINK-001"
    )

    assert (
        links[0].change.change_id
        == "PCR-LINK-001"
    )


def test_link_service_is_read_only():
    service = make_service()

    before = (
        service
        .get_change_for_case(
            "CASE-LINK-001"
        )
        .status
    )

    _ = service.get_link(
        "CASE-LINK-001"
    )

    after = (
        service
        .get_change_for_case(
            "CASE-LINK-001"
        )
        .status
    )

    assert after == before