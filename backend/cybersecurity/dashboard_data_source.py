"""
Dashboard-backed demo cybersecurity data source.

This adapter represents controlled cybersecurity observations
displayed by the EasyChatBot Cybersecurity Operations Center.

Purpose:
- provide controlled DEMO security observations;
- validate Agent 1 end-to-end flow;
- keep the Cybersecurity Intelligence Agent independent
  from the underlying data source.

This does NOT:
- connect security products;
- fetch live security information;
- execute remediation;
- modify infrastructure;
- make security decisions.

Future production implementations can replace this adapter
with SIEM, vulnerability management, IAM, GRC, cloud-security,
or other approved providers implementing the same contract.
"""

from __future__ import annotations

from backend.cybersecurity.data_source import (
    CybersecurityDataSource,
)

from backend.cybersecurity.intelligence_models import (
    CybersecuritySignal,
)


class DashboardCybersecurityDataSource(
    CybersecurityDataSource
):
    """
    Controlled DEMO implementation of
    CybersecurityDataSource.
    """

    def __init__(self) -> None:
        super().__init__(
            source_id="cybersecurity_dashboard_demo",
        )

    async def get_signals(
        self,
    ) -> list[CybersecuritySignal]:
        """
        Return controlled cybersecurity demonstration signals.

        These observations are static DEMO data and do not
        represent live production security telemetry.
        """

        return [
            CybersecuritySignal(
                signal_id="CYBER-DEMO-001",
                category="AI Security",
                title="AI prompt injection attempt detected",
                severity="high",
                confidence=0.96,
                source=(
                    "Cybersecurity Operations Center Demo"
                ),
                affected_area="AI Runtime",
                technique="Prompt Injection",
                status="open",
                metadata={
                    "environment": "DEMO",
                    "demo": True,
                },
            ),
            CybersecuritySignal(
                signal_id="CYBER-DEMO-002",
                category="Access Security",
                title="Suspicious API access detected",
                severity="medium",
                confidence=0.89,
                source=(
                    "Cybersecurity Operations Center Demo"
                ),
                affected_area="API Gateway",
                technique="Suspicious API Access",
                status="open",
                metadata={
                    "environment": "DEMO",
                    "demo": True,
                },
            ),
            CybersecuritySignal(
                signal_id="CYBER-DEMO-003",
                category="Vulnerability",
                title="Dependency vulnerability identified",
                severity="low",
                confidence=0.94,
                source=(
                    "Cybersecurity Operations Center Demo"
                ),
                affected_area="Application Dependencies",
                technique="Known Vulnerability",
                status="open",
                metadata={
                    "environment": "DEMO",
                    "demo": True,
                },
            ),
            CybersecuritySignal(
                signal_id="CYBER-DEMO-004",
                category="AI Governance",
                title="AI governance review requires attention",
                severity="medium",
                confidence=0.91,
                source=(
                    "Cybersecurity Operations Center Demo"
                ),
                affected_area="AI Governance",
                technique="Governance Control Review",
                status="open",
                metadata={
                    "environment": "DEMO",
                    "demo": True,
                },
            ),
        ]