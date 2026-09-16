from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

from app.application.persistence_operations.environment import (
    PersistenceEnvironmentNotConfigured,
)
from app.infrastructure.persistence_operations.alembic_diagnostics import inspect_migrations
from app.infrastructure.persistence_operations.postgres_diagnostics import (
    inspect_database_operations,
    inspect_postgres,
    inspect_schema,
)


class PersistenceDiagnosticsService:
    """Build live, read-only persistence diagnostics for the Operations Center."""

    def __init__(
        self,
        *,
        metadata: Any,
        project_root: Path,
        engine_resolver: Callable[[str], Any] | None = None,
        engine: Any | None = None,
    ) -> None:
        if engine_resolver is None and engine is None:
            raise ValueError("Provide engine_resolver or engine.")

        self._metadata = metadata
        self._project_root = project_root.resolve()
        if engine_resolver is not None:
            self._engine_resolver = engine_resolver
        else:
            # Backward-compatible single-engine integration is deliberately
            # restricted to DEV so an environment selector cannot imply a
            # different database when one does not exist.
            self._engine_resolver = self._single_engine_resolver(engine)

    @staticmethod
    def _single_engine_resolver(engine: Any) -> Callable[[str], Any]:
        def resolve(environment: str) -> Any:
            if environment != "dev":
                raise PersistenceEnvironmentNotConfigured(
                    "Only the DEV persistence environment is configured."
                )
            return engine

        return resolve

    def _resolve_engine(self, environment: str) -> Any:
        return self._engine_resolver(environment)

    def snapshot(self, *, environment: str) -> dict[str, Any]:
        checked_at = datetime.now(timezone.utc)
        try:
            engine = self._resolve_engine(environment)
        except PersistenceEnvironmentNotConfigured as exc:
            return self._unconfigured_snapshot(environment, checked_at, str(exc))

        database = inspect_postgres(engine, environment=environment)
        if not database["connected"]:
            migration = {
                "graph": "UNKNOWN",
                "database_revisions": [],
                "repository_heads": [],
                "missing_revisions": [],
                "pending_migrations": None,
                "drift": True,
                "migration_safety": [],
                "migration_history": [],
                "checked_at": checked_at.isoformat(),
                "error": "Database is unavailable; migration state could not be validated.",
            }
            schema = {
                "state": "UNKNOWN",
                "tables_inspected": 0,
                "tables_with_drift": 0,
                "differences": [],
                "checked_at": checked_at.isoformat(),
                "error": "Database is unavailable; schema could not be inspected.",
            }
        else:
            migration = inspect_migrations(
                engine,
                project_root=self._project_root,
            )
            schema = inspect_schema(
                engine,
                self._metadata,
                checked_at=checked_at,
            )

        compatibility = self._compatibility(migration, environment=environment)
        last_action = self._last_control_action(engine) if database["connected"] else None
        recommendation = self._recommend(
            database=database,
            migration=migration,
            schema=schema,
            compatibility=compatibility,
        )
        return {
            "environment": environment,
            "checked_at": checked_at.isoformat(),
            "database": database,
            "migration": migration,
            "schema": schema,
            "compatibility": compatibility,
            "last_action": last_action,
            "recommendation": recommendation,
        }

    def health_snapshot(self, *, environment: str) -> dict[str, Any]:
        try:
            engine = self._resolve_engine(environment)
        except PersistenceEnvironmentNotConfigured as exc:
            return {
                "environment": environment,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "database": {
                    "connected": False,
                    "environment": environment,
                    "error": str(exc),
                },
                "status": "NOT_CONFIGURED",
                "error": str(exc),
                "performance": {},
                "locks": {},
                "indexes": {},
                "maintenance": {},
                "backup_recovery": {},
                "integrity": {},
                "security": {},
                "replication": {},
                "recent_activity": [],
            }

        database = inspect_postgres(engine, environment=environment)
        operations = (
            inspect_database_operations(engine)
            if database["connected"]
            else {
                "performance": {},
                "locks": {},
                "indexes": {},
                "maintenance": {},
                "backup_recovery": {},
                "integrity": {},
                "security": {},
                "replication": {},
                "recent_activity": [],
                "error": "Database unavailable.",
            }
        )
        return {
            "environment": environment,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "database": database,
            "status": "AVAILABLE" if database["connected"] else "ERROR",
            **operations,
        }

    @staticmethod
    def _unconfigured_snapshot(
        environment: str,
        checked_at: datetime,
        error: str,
    ) -> dict[str, Any]:
        database = {
            "connected": False,
            "environment": environment,
            "database": None,
            "host": None,
            "port": None,
            "postgres_version": None,
            "latency_ms": None,
            "database_size_bytes": None,
            "active_connections": None,
            "max_connections": None,
            "connection_utilisation_pct": None,
            "uptime": None,
            "ssl_enabled": None,
            "checked_at": checked_at.isoformat(),
            "error": error,
        }
        migration = {
            "graph": "UNKNOWN",
            "database_revisions": [],
            "repository_heads": [],
            "missing_revisions": [],
            "pending_migrations": None,
            "drift": True,
            "migration_safety": [],
            "migration_history": [],
            "checked_at": checked_at.isoformat(),
            "error": error,
        }
        schema = {
            "state": "UNKNOWN",
            "tables_inspected": 0,
            "tables_with_drift": 0,
            "differences": [],
            "checked_at": checked_at.isoformat(),
            "error": error,
        }
        compatibility = {
            "application_version": None,
            "expected_schema_revision": None,
            "actual_database_revisions": [],
            "state": "NOT_CONFIGURED",
            "source": "environment database mapping",
        }
        return {
            "environment": environment,
            "checked_at": checked_at.isoformat(),
            "database": database,
            "migration": migration,
            "schema": schema,
            "compatibility": compatibility,
            "last_action": None,
            "recommendation": {
                "severity": "HIGH",
                "timing": "DO_NOW",
                "title": "Persistence environment is not configured",
                "summary": error,
                "why": "The selected environment must resolve to an explicit database connection.",
                "impact": "Diagnostics cannot prove the state of this environment.",
                "next_actions": [
                    "Configure the environment database mapping",
                    "Refresh diagnostics",
                    "Validate the database",
                ],
                "blocked_actions": [
                    "Treat this environment as healthy",
                    "Apply migrations",
                    "Promote a persistence-dependent release",
                ],
            },
        }

    def _compatibility(
        self,
        migration: dict[str, Any],
        *,
        environment: str,
    ) -> dict[str, Any]:
        heads = migration["repository_heads"]
        actual = migration["database_revisions"]
        configured_expected = (
            self._env(f"PERSISTENCE_EXPECTED_SCHEMA_REVISION_{environment.upper()}")
            or self._env("PERSISTENCE_EXPECTED_SCHEMA_REVISION")
        )
        expected_revision = configured_expected or (heads[0] if len(heads) == 1 else None)
        compatible = (
            bool(expected_revision and expected_revision in actual)
            and not migration["drift"]
            and migration["graph"] == "IN_SYNC"
        )
        return {
            "application_version": self._env(f"APP_VERSION_{environment.upper()}")
            or self._env("APP_VERSION"),
            "expected_schema_revision": expected_revision,
            "actual_database_revisions": actual,
            "state": (
                "COMPATIBLE"
                if compatible
                else "OUT_OF_SYNC"
                if expected_revision
                else "NOT_CONFIGURED"
            ),
            "source": (
                f"PERSISTENCE_EXPECTED_SCHEMA_REVISION_{environment.upper()}"
                " / repository head"
            ),
        }

    @staticmethod
    def _env(name: str) -> str | None:
        value = os.getenv(name)
        return value.strip() if value and value.strip() else None

    @staticmethod
    def _last_control_action(engine: Any) -> dict[str, Any] | None:
        try:
            with engine.connect() as connection:
                row = connection.execute(
                    text(
                        """
                        SELECT functionality_id, environment, action,
                               availability, actor, reason, changed_at
                        FROM functionality_control_audit
                        ORDER BY changed_at DESC, id DESC
                        LIMIT 1
                        """
                    )
                ).mappings().first()
                if row is None:
                    return None
                return {
                    "source": "functionality_control_audit",
                    "functionality_id": row["functionality_id"],
                    "environment": row["environment"],
                    "action": row["action"],
                    "availability": row["availability"],
                    "actor": row["actor"],
                    "reason": row["reason"],
                    "changed_at": (
                        row["changed_at"].isoformat()
                        if row["changed_at"]
                        else None
                    ),
                }
        except Exception:
            # This audit table is optional to the persistence diagnostic slice.
            return None

    @staticmethod
    def _recommend(
        *,
        database: dict[str, Any],
        migration: dict[str, Any],
        schema: dict[str, Any],
        compatibility: dict[str, Any],
    ) -> dict[str, Any]:
        if not database["connected"]:
            return {
                "severity": "HIGH",
                "timing": "DO_NOW",
                "title": "Database unavailable",
                "summary": "Persistence diagnostics cannot reach PostgreSQL.",
                "why": "Live operational facts cannot be trusted while the database connection is unavailable.",
                "impact": "Persistence-dependent functionality may be unavailable.",
                "next_actions": [
                    "Restore database connectivity",
                    "Refresh diagnostics",
                    "Validate the database",
                ],
                "blocked_actions": [
                    "Apply migrations",
                    "Promote a persistence-dependent release",
                ],
            }
        if migration["graph"] in {"ERROR", "INCONSISTENT"}:
            missing = ", ".join(migration["missing_revisions"]) or "unresolved migration state"
            return {
                "severity": "CRITICAL",
                "timing": "STOP_DO_NOT_PROCEED",
                "title": "Migration history requires reconciliation",
                "summary": (
                    "The migration graph cannot be trusted: "
                    f"{missing}."
                ),
                "why": "Applying another migration before reconciling the migration graph can make migration history less reliable.",
                "impact": "Migration execution and persistence promotion must remain blocked until lineage is understood.",
                "next_actions": [
                    "Review migration lineage",
                    "Generate reconciliation plan",
                    "Review and approve the plan",
                    "Re-validate the migration graph",
                ],
                "blocked_actions": [
                    "Apply migrations",
                    "Stamp an arbitrary revision",
                    "Modify alembic_version manually",
                    "Promote deployment",
                ],
            }
        if schema["state"] == "DRIFT_DETECTED":
            return {
                "severity": "HIGH",
                "timing": "BEFORE_NEXT_DEPLOYMENT",
                "title": "Schema drift detected",
                "summary": (
                    f"{schema['tables_with_drift']} table(s) differ from "
                    "registered application metadata."
                ),
                "why": "The running application and database must agree on persistent structure before dependent changes are promoted.",
                "impact": "Persistence operations may fail or behave differently from the application contract.",
                "next_actions": [
                    "Review schema differences",
                    "Generate migration plan",
                    "Test in DEV",
                    "Validate after applying",
                ],
                "blocked_actions": ["Apply an unreviewed migration"],
            }
        if compatibility["state"] == "OUT_OF_SYNC":
            return {
                "severity": "HIGH",
                "timing": "BEFORE_NEXT_DEPLOYMENT",
                "title": "Application and database are out of sync",
                "summary": "The configured application/schema compatibility contract is not satisfied.",
                "why": "A deployment must not assume schema capabilities that are absent from its target database.",
                "impact": "A release may fail at runtime or expose inconsistent persistence behaviour.",
                "next_actions": [
                    "Review application/schema compatibility",
                    "Align the environment",
                    "Validate before promotion",
                ],
                "blocked_actions": ["Promote incompatible release"],
            }
        if migration["graph"] == "PENDING":
            count = len(migration["pending_migrations"] or [])
            return {
                "severity": "MEDIUM",
                "timing": "BEFORE_NEXT_DEPLOYMENT",
                "title": "Migration required",
                "summary": f"{count} migration revision(s) are ahead of the database.",
                "why": "The repository contains database changes that have not yet been applied to this environment.",
                "impact": "Dependent application changes should not be promoted until the environment is migrated.",
                "next_actions": [
                    "Review pending migrations",
                    "Review migration risk",
                    "Test in DEV",
                    "Apply approved migration",
                    "Validate schema",
                ],
                "blocked_actions": [],
            }
        return {
            "severity": "INFO",
            "timing": "NO_ACTION_REQUIRED",
            "title": "Persistence is in sync",
            "summary": "Database connectivity, migration state and registered schema are consistent.",
            "why": "No persistence change is currently required.",
            "impact": "No current persistence issue detected.",
            "next_actions": [
                "Continue normal development",
                "Refresh diagnostics when persistence changes",
            ],
            "blocked_actions": [],
        }


