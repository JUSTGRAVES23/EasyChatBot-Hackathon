from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.application.privacy.privacy_governance_case import (
    PrivacyGovernanceCase,
    PrivacyTriggerType,
)
from app.application.privacy.privacy_governance_case_registry import (
    PrivacyGovernanceCaseRegistry,
)
from app.project_control_center.domain.models import (
    Severity,
    SourceStatus,
)
from app.project_control_center.infrastructure.governance_risk_source import (
    GovernanceRiskProjectStatusSource,
)


def make_case(
    *,
    case_id: str,
    risk: str,
    governance_status: str = "PENDING_DPO_GRC",
) -> PrivacyGovernanceCase:
    return PrivacyGovernanceCase(
        case_id=case_id,
        title=f"Privacy case {case_id}",
        summary="Test privacy governance case",
        trigger_type=PrivacyTriggerType.NEW_PROCESSING,
        triggered_at=datetime.now(timezone.utc),
        trigger_source="test",
        change_id=f"CHANGE-{case_id}",
        risk=risk,
        governance_status=governance_status,
    )


def test_source_identity() -> None:
    registry = PrivacyGovernanceCaseRegistry()

    source = GovernanceRiskProjectStatusSource(
        case_registry=registry,
    )

    assert source.source_id == "privacy-governance"
    assert source.source_name == "Privacy Governance"


def test_health_reports_available() -> None:
    registry = PrivacyGovernanceCaseRegistry()

    source = GovernanceRiskProjectStatusSource(
        case_registry=registry,
    )

    result = source.health()

    assert result.source_id == "privacy-governance"
    assert result.name == "Privacy Governance"
    assert result.status is SourceStatus.AVAILABLE


def test_fetch_risks_maps_privacy_case_risk() -> None:
    registry = PrivacyGovernanceCaseRegistry(
        [
            make_case(
                case_id="CASE-LOW",
                risk="low",
            ),
            make_case(
                case_id="CASE-MEDIUM",
                risk="medium",
            ),
            make_case(
                case_id="CASE-HIGH",
                risk="high",
            ),
        ]
    )

    source = GovernanceRiskProjectStatusSource(
        case_registry=registry,
    )

    risks = source.fetch_risks("easychatbot")

    assert len(risks) == 3

    by_id = {
        risk.risk_id: risk
        for risk in risks
    }

    assert by_id["CASE-LOW"].severity is Severity.LOW
    assert by_id["CASE-MEDIUM"].severity is Severity.MEDIUM
    assert by_id["CASE-HIGH"].severity is Severity.HIGH


def test_fetch_risks_preserves_governance_status_separately() -> None:
    registry = PrivacyGovernanceCaseRegistry(
        [
            make_case(
                case_id="CASE-1",
                risk="high",
                governance_status="PENDING_DPO_GRC",
            ),
            make_case(
                case_id="CASE-2",
                risk="high",
                governance_status="APPROVED",
            ),
            make_case(
                case_id="CASE-3",
                risk="high",
                governance_status="BLOCKED",
            ),
        ]
    )

    source = GovernanceRiskProjectStatusSource(
        case_registry=registry,
    )

    risks = source.fetch_risks("easychatbot")

    by_id = {
        risk.risk_id: risk
        for risk in risks
    }

    assert by_id["CASE-1"].severity is Severity.HIGH
    assert by_id["CASE-1"].status == "PENDING_DPO_GRC"

    assert by_id["CASE-2"].severity is Severity.HIGH
    assert by_id["CASE-2"].status == "APPROVED"

    assert by_id["CASE-3"].severity is Severity.HIGH
    assert by_id["CASE-3"].status == "BLOCKED"


def test_fetch_risks_preserves_project_and_source_identity() -> None:
    registry = PrivacyGovernanceCaseRegistry(
        [
            make_case(
                case_id="CASE-TRACE",
                risk="medium",
            )
        ]
    )

    source = GovernanceRiskProjectStatusSource(
        case_registry=registry,
    )

    risks = source.fetch_risks("project-123")

    assert len(risks) == 1
    risk = risks[0]

    assert risk.project_id == "project-123"
    assert risk.risk_id == "CASE-TRACE"
    assert risk.title == "Privacy case CASE-TRACE"
    assert risk.source == "privacy-governance"
    assert risk.workstream_id is None
    assert risk.owner is None


def test_fetch_risks_is_read_only() -> None:
    case = make_case(
        case_id="CASE-READONLY",
        risk="high",
    )

    registry = PrivacyGovernanceCaseRegistry([case])

    source = GovernanceRiskProjectStatusSource(
        case_registry=registry,
    )

    before = registry.all()

    source.fetch_risks("easychatbot")

    after = registry.all()

    assert after == before
    assert after[0] == case


@pytest.mark.parametrize(
    "method_name",
    [
        "fetch_workstreams",
        "fetch_metrics",
        "fetch_issues",
        "fetch_actions",
        "fetch_milestones",
    ],
)
def test_non_risk_project_contracts_remain_empty(
    method_name: str,
) -> None:
    registry = PrivacyGovernanceCaseRegistry()

    source = GovernanceRiskProjectStatusSource(
        case_registry=registry,
    )

    method = getattr(source, method_name)

    assert method("easychatbot") == []


def test_unknown_risk_fails_closed_to_medium() -> None:
    registry = PrivacyGovernanceCaseRegistry(
        [
            make_case(
                case_id="CASE-UNKNOWN",
                risk="unexpected-risk",
            )
        ]
    )

    source = GovernanceRiskProjectStatusSource(
        case_registry=registry,
    )

    risks = source.fetch_risks("easychatbot")

    assert len(risks) == 1
    assert risks[0].severity is Severity.MEDIUM


def test_none_registry_is_rejected() -> None:
    with pytest.raises(ValueError, match="case_registry cannot be None"):
        GovernanceRiskProjectStatusSource(
            case_registry=None,  # type: ignore[arg-type]
        )
