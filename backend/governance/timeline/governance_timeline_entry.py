from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class GovernanceTimelineEntry:
    event_id: str
    event: str
    component: str
    actor: str
    reason: str
    severity: str
    evidence_available: bool = True
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
