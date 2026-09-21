from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

class DiscoveryCandidateStatus(str, Enum):
    DISCOVERED = "discovered"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REGISTERED = "registered"

@dataclass(frozen=True, slots=True)
class ProjectDiscoveryCandidate:
    candidate_id: str
    candidate_key: str
    name: str
    description: str = ""
    owner: str | None = None
    source: str = ""
    source_reference: str | None = None
    status: DiscoveryCandidateStatus = DiscoveryCandidateStatus.DISCOVERED
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: datetime | None = None
    registered_project_id: str | None = None

__all__ = ["DiscoveryCandidateStatus", "ProjectDiscoveryCandidate"]
