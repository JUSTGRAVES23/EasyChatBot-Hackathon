"""
EasyChatBot Cybersecurity Operations Center schemas.

API contract models only.

No business logic.
"""

from pydantic import BaseModel
from typing import List


class ThreatActivitySchema(BaseModel):

    severity: str

    count: int



class SecurityEventSchema(BaseModel):

    time: str

    message: str

    severity: str



class ComplianceFrameworkSchema(BaseModel):

    name: str

    score: int



class RiskOverviewSchema(BaseModel):

    critical: int

    high: int

    medium: int

    low: int



class CyberSecurityDashboardSchema(BaseModel):

    security_score: int

    active_threats: int

    vulnerabilities: int

    escalations_today: int

    threat_activity: List[ThreatActivitySchema]

    security_events: List[SecurityEventSchema]

    risk_overview: RiskOverviewSchema

    compliance_frameworks: List[ComplianceFrameworkSchema]