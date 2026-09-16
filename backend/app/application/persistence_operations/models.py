from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class PersistenceRecommendation:
    severity: str
    timing: str
    title: str
    summary: str
    why: str
    impact: str
    next_actions: list[str]
    blocked_actions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PersistenceSnapshot:
    environment: str
    checked_at: datetime
    database: dict[str, Any]
    migration: dict[str, Any]
    schema: dict[str, Any]
    compatibility: dict[str, Any]
    last_action: dict[str, Any] | None
    recommendation: PersistenceRecommendation


@dataclass(frozen=True)
class DatabaseHealthSnapshot:
    environment: str
    checked_at: datetime
    status: str
    database: dict[str, Any]
    performance: dict[str, Any]
    locks: dict[str, Any]
    indexes: dict[str, Any]
    maintenance: dict[str, Any]
    backup_recovery: dict[str, Any]
    integrity: dict[str, Any]
    security: dict[str, Any]
    replication: dict[str, Any]
    recent_activity: list[dict[str, Any]]
