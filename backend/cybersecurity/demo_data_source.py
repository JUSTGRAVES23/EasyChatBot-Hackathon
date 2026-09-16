"""
Controlled demo cybersecurity data source.

This is explicitly simulated data for hackathon demonstration purposes.

It does not:
- call external security systems;
- fetch live security data;
- execute remediation;
- modify infrastructure.

It exists to validate the Cybersecurity Intelligence Agent
pipeline with controlled observations.
"""

from __future__ import annotations


from cybersecurity.data_source import (
    CybersecurityDataSource,
)

from cybersecurity.intelligence_models import (
    CybersecuritySignal,
)



class DemoCybersecurityDataSource(
    CybersecurityDataSource
):
    """
    Returns controlled simulated security observations.

    This is a replaceable demo adapter.

    Production implementations can replace it with
    approved security data providers.
    """


    def __init__(self) -> None:

        super().__init__(
            source_id="cybersecurity_demo"
        )



    async def get_signals(
        self,
    ) -> list[CybersecuritySignal]:
        """
        Return simulated cybersecurity signals.
        """

        return [

            CybersecuritySignal(
                signal_id="demo-threat-001",
                category="threat",
                title=(
                    "AI prompt injection attempt detected"
                ),
                severity="high",
                confidence=0.96,
                source="demo-security-events",
                affected_area=(
                    "AI interaction layer"
                ),
                technique="Prompt Injection",
                status="open",
            ),


            CybersecuritySignal(
                signal_id="demo-vuln-001",
                category="vulnerability",
                title=(
                    "Critical dependency vulnerability identified"
                ),
                severity="critical",
                confidence=0.98,
                source="demo-vulnerability-scanner",
                affected_area=(
                    "Application dependencies"
                ),
                technique="Known Vulnerability",
                status="open",
            ),


            CybersecuritySignal(
                signal_id="demo-identity-001",
                category="identity",
                title=(
                    "Suspicious privileged API access detected"
                ),
                severity="high",
                confidence=0.91,
                source="demo-identity-monitor",
                affected_area=(
                    "Privileged API access"
                ),
                technique="Anomalous Access",
                status="open",
            ),


            CybersecuritySignal(
                signal_id="demo-governance-001",
                category="governance",
                title=(
                    "AI governance review requires attention"
                ),
                severity="medium",
                confidence=0.87,
                source="demo-governance-monitor",
                affected_area=(
                    "AI governance"
                ),
                technique="Control Review",
                status="open",
            ),


            CybersecuritySignal(
                signal_id="demo-event-001",
                category="security_event",
                title=(
                    "Dependency security event under investigation"
                ),
                severity="low",
                confidence=0.89,
                source="demo-security-events",
                affected_area=(
                    "Application"
                ),
                technique="Security Event",
                status="open",
            ),

        ]
