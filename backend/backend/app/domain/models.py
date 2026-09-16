from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ProjectStatus(str, Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BLOCKED = "blocked"
    COMPLETE = "complete"
    UNKNOWN = "unknown"


class WorkstreamStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    BLOCKED = "blocked"
    COMPLETE = "complete"
    UNKNOWN = "unknown"


class SourceStatus(str, Enum):
    AVAILABLE = "available"
    STALE = "stale"
    UNAVAILABLE = "unavailable"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ActionStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class ProjectEventType(str, Enum):
    PROJECT_CREATED = "project_created"
    WORKSTREAM_UPDATED = "workstream_updated"
    ISSUE_OPENED = "issue_opened"
    ISSUE_RESOLVED = "issue_resolved"
    RISK_OPENED = "risk_opened"
    RISK_RESOLVED = "risk_resolved"
    MILESTONE_COMPLETED = "milestone_completed"
    ACTION_CREATED = "action_created"
    ACTION_COMPLETED = "action_completed"
    APPROVAL_GRANTED = "approval_granted"
    READINESS_CHANGED = "readiness_changed"


@dataclass(frozen=True, slots=True)
class WorkstreamSnapshot:
    workstream_id: str
    name: str
    completion_percent: float | None
    status: WorkstreamStatus
    source: str
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class MetricSnapshot:
    key: str
    label: str
    value: float | int | str
    unit: str | None = None
    source: str = ""
    observed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class IssueSnapshot:
    issue_id: str
    project_id: str
    title: str
    severity: Severity
    status: IssueStatus
    workstream_id: str | None = None
    owner: str | None = None
    source: str = ""


@dataclass(frozen=True, slots=True)
class RiskSnapshot:
    risk_id: str
    project_id: str
    title: str
    severity: Severity
    status: str
    workstream_id: str | None = None
    owner: str | None = None
    source: str = ""


@dataclass(frozen=True, slots=True)
class ActionSnapshot:
    action_id: str
    project_id: str
    title: str
    priority: Severity
    status: ActionStatus
    owner: str | None = None
    workstream_id: str | None = None
    due_at: datetime | None = None
    source: str = ""


@dataclass(frozen=True, slots=True)
class MilestoneSnapshot:
    milestone_id: str
    project_id: str
    name: str
    status: str
    target_date: datetime | None = None
    source: str = ""


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    source_id: str
    name: str
    status: SourceStatus
    updated_at: datetime | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectControlSnapshot:
    project_id: str
    project_name: str
    project_status: ProjectStatus
    overall_progress_percent: float | None
    current_milestone: str | None
    current_workstream: str | None
    release_readiness: str
    open_blockers: int
    open_risks: int
    workstreams: tuple[WorkstreamSnapshot, ...] = ()
    metrics: tuple[MetricSnapshot, ...] = ()
    issues: tuple[IssueSnapshot, ...] = ()
    risks: tuple[RiskSnapshot, ...] = ()
    actions: tuple[ActionSnapshot, ...] = ()
    milestones: tuple[MilestoneSnapshot, ...] = ()
    sources: tuple[SourceSnapshot, ...] = ()
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class ProjectDefinition:
    project_id: str
    name: str
    description: str = ""
    owner: str | None = None
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class ProjectEvent:
    event_id: str
    project_id: str
    event_type: ProjectEventType
    occurred_at: datetime
    summary: str
    source: str
    metadata: tuple[tuple[str, str], ...] = ()
