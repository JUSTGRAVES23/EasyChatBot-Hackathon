from __future__ import annotations

from datetime import datetime, timezone

from app.application.privacy.privacy_governance_case_registry import (
    PrivacyGovernanceCaseRegistry,
)

from ..domain.models import (
    ActionSnapshot,
    IssueSnapshot,
    MetricSnapshot,
    MilestoneSnapshot,
    RiskSnapshot,
    Severity,
    SourceSnapshot,
    SourceStatus,
    WorkstreamSnapshot,
)
from ..domain.ports import ProjectStatusSource


class GovernanceRiskProjectStatusSource(ProjectStatusSource):
    """Read-only PCD adapter over Privacy Governance risk state.

    The PrivacyGovernanceCaseRegistry remains authoritative.

    This adapter projects governance-case risk into the PCD RiskSnapshot
    contract without creating a second risk store or changing governance
    state.

    Risk severity and governance decision status remain separate concepts:

        case.risk              -> RiskSnapshot.severity
        case.governance_status -> RiskSnapshot.status
    """

    _SOURCE_ID = "privacy-governance"
    _SOURCE_NAME = "Privacy Governance"

    def __init__(
        self,
        *,
        case_registry: PrivacyGovernanceCaseRegistry,
    ) -> None:
        if case_registry is None:
            raise ValueError(
                "case_registry cannot be None."
            )

        self._case_registry = case_registry

    @property
    def source_id(self) -> str:
        return self._SOURCE_ID

    @property
    def source_name(self) -> str:
        return self._SOURCE_NAME

    def health(self) -> SourceSnapshot:
        """Report adapter availability without modifying governance state."""
        return SourceSnapshot(
            source_id=self.source_id,
            name=self.source_name,
            status=SourceStatus.AVAILABLE,
            updated_at=datetime.now(timezone.utc),
        )

    def fetch_workstreams(
        self,
        project_id: str,
    ) -> list[WorkstreamSnapshot]:
        """Privacy Governance does not own PCD project workstreams."""
        return []

    def fetch_metrics(
        self,
        project_id: str,
    ) -> list[MetricSnapshot]:
        """Privacy Governance risk cases are projected as risks, not metrics."""
        return []

    def fetch_issues(
        self,
        project_id: str,
    ) -> list[IssueSnapshot]:
        """Privacy Governance cases are represented through RiskSnapshot."""
        return []

    def fetch_risks(
        self,
        project_id: str,
    ) -> list[RiskSnapshot]:
        """Project authoritative governance cases into PCD risks."""
        risks: list[RiskSnapshot] = []

        for case in self._case_registry.all():
            risks.append(
                RiskSnapshot(
                    risk_id=case.case_id,
                    project_id=project_id,
                    title=case.title,
                    severity=self._map_severity(case.risk),
                    status=case.governance_status,
                    workstream_id=None,
                    owner=None,
                    source=self.source_id,
                )
            )

        return risks

    def fetch_actions(
        self,
        project_id: str,
    ) -> list[ActionSnapshot]:
        """Privacy Governance does not own PCD project actions."""
        return []

    def fetch_milestones(
        self,
        project_id: str,
    ) -> list[MilestoneSnapshot]:
        """Privacy Governance does not own PCD milestones."""
        return []

    @staticmethod
    def _map_severity(
        risk: str,
    ) -> Severity:
        """Normalize authoritative privacy risk into PCD severity.

        Privacy governance currently uses LOW/MEDIUM/HIGH semantics.
        Unknown values fail closed to MEDIUM rather than inventing a new
        severity or silently treating the case as LOW.
        """
        normalized = str(risk).strip().lower()

        mapping = {
            "low": Severity.LOW,
            "medium": Severity.MEDIUM,
            "high": Severity.HIGH,
        }

        return mapping.get(
            normalized,
            Severity.MEDIUM,
        )


__all__ = [
    "GovernanceRiskProjectStatusSource",
]
