from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory


def _config(project_root: Path, alembic_ini_path: Path | None = None) -> Config:
    root = project_root.resolve()
    ini_path = (alembic_ini_path or (root / "alembic.ini")).resolve()
    config = Config(str(ini_path))

    configured_location = config.get_main_option("script_location")
    if configured_location:
        # Resolve the configured location against the Alembic config directory.
        location = Path(configured_location)
        if not location.is_absolute():
            location = (ini_path.parent / location).resolve()
    else:
        location = (root / "backend" / "alembic").resolve()

    config.set_main_option("script_location", str(location))
    return config


def _repository_scripts(
    project_root: Path,
    alembic_ini_path: Path | None = None,
) -> ScriptDirectory:
    return ScriptDirectory.from_config(_config(project_root, alembic_ini_path))


def _database_revisions(connection: Any) -> list[str]:
    return sorted(MigrationContext.configure(connection).get_current_heads())


def _revision_graph(script: ScriptDirectory) -> dict[str, set[str]]:
    """Return revision -> direct parent revisions."""
    graph: dict[str, set[str]] = {}
    for revision in script.walk_revisions():
        parents = revision.down_revision
        if parents is None:
            graph[revision.revision] = set()
        elif isinstance(parents, tuple):
            graph[revision.revision] = set(parents)
        else:
            graph[revision.revision] = {parents}
    return graph


def _ancestors(revision: str, graph: dict[str, set[str]]) -> set[str]:
    found: set[str] = set()
    stack = [revision]
    while stack:
        current = stack.pop()
        for parent in graph.get(current, set()):
            if parent not in found:
                found.add(parent)
                stack.append(parent)
    return found


def _pending_revisions(
    repo_heads: list[str],
    current_heads: list[str],
    graph: dict[str, set[str]],
) -> list[str]:
    if not repo_heads:
        return []

    required: set[str] = set()
    for head in repo_heads:
        required.add(head)
        required.update(_ancestors(head, graph))

    applied: set[str] = set()
    for head in current_heads:
        applied.add(head)
        applied.update(_ancestors(head, graph))

    return sorted(required - applied)


def _migration_lineage(
    script: ScriptDirectory,
    *,
    current_heads: list[str],
    pending: list[str],
    unknown: list[str],
) -> list[dict[str, Any]]:
    graph = _revision_graph(script)
    applied: set[str] = set()
    for head in current_heads:
        applied.add(head)
        applied.update(_ancestors(head, graph))
    pending_set = set(pending)
    current_set = set(current_heads)

    history = []
    for revision in sorted(graph):
        history.append(
            {
                "revision": revision,
                "down_revision": sorted(graph[revision]),
                "status": (
                    "CURRENT"
                    if revision in current_set
                    else "APPLIED"
                    if revision in applied
                    else "PENDING"
                    if revision in pending_set
                    else "NOT_REACHED"
                ),
            }
        )
    for revision in unknown:
        history.append(
            {
                "revision": revision,
                "down_revision": [],
                "status": "UNKNOWN_DATABASE_REVISION",
            }
        )
    return history


def _migration_risk(
    script: ScriptDirectory,
    revision_ids: list[str],
) -> list[dict[str, Any]]:
    """Provide a conservative source scan; this is advisory, not execution safety."""
    findings: list[dict[str, Any]] = []
    dangerous = (
        "drop_column",
        "drop_table",
        "drop_constraint",
        "op.drop",
        "alter_column",
    )
    medium = (
        "create_index",
        "op.create_index",
        "rename",
        "add_column",
        "create_table",
    )
    for revision_id in revision_ids:
        try:
            revision = script.get_revision(revision_id)
            path = Path(revision.path) if revision.path else None
            source = path.read_text(encoding="utf-8") if path and path.exists() else ""
            lowered = source.lower()
            risk = "LOW"
            reasons: list[str] = []
            if any(token in lowered for token in dangerous):
                risk = "HIGH"
                reasons.append("Potentially destructive or lock-sensitive DDL detected.")
            elif any(token in lowered for token in medium):
                risk = "MEDIUM"
                reasons.append("Schema/index change detected; review before promotion.")
            findings.append(
                {
                    "revision": revision_id,
                    "risk": risk,
                    "reasons": reasons,
                    "analysis_mode": "HEURISTIC_SOURCE_SCAN",
                }
            )
        except Exception as exc:
            findings.append(
                {
                    "revision": revision_id,
                    "risk": "UNKNOWN",
                    "reasons": [
                        f"Unable to inspect migration source: {type(exc).__name__}"
                    ],
                    "analysis_mode": "HEURISTIC_SOURCE_SCAN",
                }
            )
    return findings


def inspect_migrations(
    engine: Any,
    *,
    project_root: Path,
    alembic_ini_path: Path | None = None,
) -> dict[str, Any]:
    checked_at = datetime.now(timezone.utc)
    try:
        script = _repository_scripts(project_root, alembic_ini_path)
        with engine.connect() as connection:
            db_revisions = _database_revisions(connection)

        repo_heads = sorted(script.get_heads())
        graph = _revision_graph(script)
        known_revisions = set(graph)
        missing = sorted(
            revision for revision in db_revisions if revision not in known_revisions
        )

        # A database state with two heads where one is an ancestor of the other
        # is suspicious and should never be treated as clean.
        current_ancestor_conflict = any(
            a != b and a in _ancestors(b, graph)
            for a in db_revisions
            for b in db_revisions
        )

        if missing or current_ancestor_conflict:
            graph_state = "INCONSISTENT"
            pending: list[str] | None = None
        else:
            pending_list = _pending_revisions(repo_heads, db_revisions, graph)
            graph_state = "IN_SYNC" if not pending_list else "PENDING"
            pending = pending_list

        candidate_revisions = pending or []
        return {
            "graph": graph_state,
            "database_revisions": db_revisions,
            "repository_heads": repo_heads,
            "missing_revisions": missing,
            "pending_migrations": pending,
            "drift": graph_state == "INCONSISTENT",
            "migration_safety": _migration_risk(script, candidate_revisions),
            "migration_history": _migration_lineage(
                script,
                current_heads=db_revisions,
                pending=candidate_revisions,
                unknown=missing,
            ),
            "checked_at": checked_at.isoformat(),
            "error": None,
        }
    except Exception as exc:
        return {
            "graph": "ERROR",
            "database_revisions": [],
            "repository_heads": [],
            "missing_revisions": [],
            "pending_migrations": None,
            "drift": True,
            "migration_safety": [],
            "migration_history": [],
            "checked_at": checked_at.isoformat(),
            "error": f"{type(exc).__name__}: migration diagnostics could not be completed.",
        }
