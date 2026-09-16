from __future__ import annotations

import os
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from sqlalchemy import inspect, text


QUERY_TEXT_REDACTION = (
    "[REDACTED — enable PERSISTENCE_EXPOSE_QUERY_TEXT for authorised diagnostics]"
)


def _scalar(connection: Any, sql: str, default: Any = None) -> Any:
    try:
        return connection.execute(text(sql)).scalar_one_or_none()
    except Exception:
        return default


def _rows(connection: Any, sql: str) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in connection.execute(text(sql)).mappings().all()]
    except Exception:
        return []


def _safe_error(exc: Exception) -> str:
    """Return diagnostics-safe error text without SQL, DSNs or provider details."""
    return f"{type(exc).__name__}: diagnostic query failed."


def _setting(connection: Any, name: str) -> str | None:
    # Names passed here are constants owned by this module, never user input.
    return _scalar(
        connection,
        f"SELECT current_setting('{name}', true)",
        None,
    )


def _redact_query(value: Any) -> str:
    if os.getenv("PERSISTENCE_EXPOSE_QUERY_TEXT", "false").lower() in {
        "1",
        "true",
        "yes",
    }:
        return str(value)
    return QUERY_TEXT_REDACTION


def inspect_postgres(engine: Any, *, environment: str) -> dict[str, Any]:
    checked_at = datetime.now(timezone.utc)
    started = perf_counter()
    try:
        with engine.connect() as connection:
            version = _scalar(connection, "SELECT version()")
            database = _scalar(connection, "SELECT current_database()")
            host = _scalar(connection, "SELECT inet_server_addr()::text")
            port = _scalar(connection, "SELECT inet_server_port()")
            size = _scalar(
                connection,
                "SELECT pg_database_size(current_database())",
            )
            max_connections = _scalar(
                connection,
                "SELECT current_setting('max_connections')::integer",
            )
            backends = _scalar(
                connection,
                """
                SELECT numbackends
                FROM pg_stat_database
                WHERE datname = current_database()
                """,
            )
            uptime = _scalar(
                connection,
                "SELECT now() - pg_postmaster_start_time()",
            )
            ssl = _scalar(
                connection,
                """
                SELECT ssl
                FROM pg_stat_ssl
                WHERE pid = pg_backend_pid()
                """,
                None,
            )
            latency_ms = round((perf_counter() - started) * 1000, 2)
            return {
                "connected": True,
                "environment": environment,
                "database": database,
                "host": host,
                "port": port,
                "postgres_version": version,
                "latency_ms": latency_ms,
                "database_size_bytes": size,
                "active_connections": backends,
                "max_connections": max_connections,
                "connection_utilisation_pct": (
                    round((backends / max_connections) * 100, 2)
                    if backends is not None and max_connections
                    else None
                ),
                "uptime": str(uptime) if uptime is not None else None,
                "ssl_enabled": ssl if ssl is None else bool(ssl),
                "checked_at": checked_at.isoformat(),
                "error": None,
            }
    except Exception as exc:
        return {
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
            "error": _safe_error(exc),
        }


def inspect_database_operations(engine: Any) -> dict[str, Any]:
    """Collect safe, read-only PostgreSQL operational facts.

    Optional PostgreSQL statistics are reported as unavailable rather than
    being replaced with fabricated values when the required extension or
    privilege is missing.
    """
    checked_at = datetime.now(timezone.utc)
    result: dict[str, Any] = {
        "checked_at": checked_at.isoformat(),
        "performance": {
            "status": "NOT_AVAILABLE",
            "cache_hit_ratio_pct": None,
            "transactions_committed": None,
            "transactions_rolled_back": None,
            "rows_returned": None,
            "rows_fetched": None,
            "query_statistics": "NOT_AVAILABLE",
            "slow_queries": [],
        },
        "locks": {
            "status": "NOT_AVAILABLE",
            "blocking_detected": False,
            "blocked_queries": [],
            "long_running_transactions": [],
            "active_transactions": None,
        },
        "indexes": {
            "status": "NOT_AVAILABLE",
            "total_indexes": None,
            "unused_indexes": [],
            "unused_index_count": None,
            "invalid_indexes": None,
            "largest_indexes": [],
        },
        "maintenance": {
            "status": "NOT_AVAILABLE",
            "tables": [],
            "tables_with_dead_tuples": None,
            "autovacuum": None,
            "track_counts": None,
        },
        "backup_recovery": {
            "backup_integration": "NOT_CONFIGURED",
            "last_backup": None,
            "backup_status": "UNKNOWN",
            "restore_verification": "NOT_AVAILABLE",
            "point_in_time_recovery": "NOT_CONFIRMED",
            "archive_mode": None,
            "wal_level": None,
        },
        "integrity": {
            "status": "AVAILABLE",
            "foreign_key_constraints": None,
            "check_constraints": None,
            "application_integrity_checks": "NOT_CONFIGURED",
        },
        "security": {
            "status": "NOT_AVAILABLE",
            "current_role": None,
            "ssl_enabled": None,
            "is_superuser": None,
            "can_create_role": None,
            "can_create_database": None,
            "can_login": None,
            "pg_hba_analysis": "NOT_AVAILABLE_FROM_APPLICATION_ROLE",
        },
        "replication": {
            "status": "NOT_AVAILABLE",
            "is_standby": None,
            "replica_count": None,
            "wal_level": None,
            "archive_mode": None,
        },
        "recent_activity": [],
        "error": None,
    }

    try:
        with engine.connect() as connection:
            db_stats = _rows(
                connection,
                """
                SELECT numbackends, xact_commit, xact_rollback,
                       blks_read, blks_hit, tup_returned, tup_fetched,
                       stats_reset
                FROM pg_stat_database
                WHERE datname = current_database()
                """,
            )
            if db_stats:
                stats = db_stats[0]
                total_blocks = (stats.get("blks_read") or 0) + (
                    stats.get("blks_hit") or 0
                )
                cache_hit = (
                    round(
                        (stats.get("blks_hit") or 0) / total_blocks * 100,
                        2,
                    )
                    if total_blocks
                    else None
                )
                result["performance"].update(
                    {
                        "status": "AVAILABLE",
                        "cache_hit_ratio_pct": cache_hit,
                        "transactions_committed": stats.get("xact_commit"),
                        "transactions_rolled_back": stats.get("xact_rollback"),
                        "rows_returned": stats.get("tup_returned"),
                        "rows_fetched": stats.get("tup_fetched"),
                    }
                )

            extension_version = _scalar(
                connection,
                """
                SELECT extversion
                FROM pg_extension
                WHERE extname = 'pg_stat_statements'
                """,
                None,
            )
            if extension_version:
                slow = _rows(
                    connection,
                    """
                    SELECT round(mean_exec_time::numeric, 2) AS mean_ms,
                           calls,
                           round(total_exec_time::numeric, 2) AS total_ms,
                           left(query, 180) AS query
                    FROM pg_stat_statements
                    ORDER BY mean_exec_time DESC
                    LIMIT 5
                    """,
                )
                for row in slow:
                    row["query"] = _redact_query(row.get("query"))
                result["performance"]["query_statistics"] = (
                    f"AVAILABLE ({extension_version})"
                    if slow or extension_version
                    else "NOT_AVAILABLE"
                )
                result["performance"]["slow_queries"] = slow
            else:
                result["performance"]["query_statistics"] = "NOT_CONFIGURED"

            blocking = _rows(
                connection,
                """
                SELECT a.pid AS blocked_pid,
                       a.usename AS blocked_user,
                       a.query AS blocked_query,
                       a.wait_event_type,
                       a.wait_event,
                       pg_blocking_pids(a.pid) AS blocking_pids
                FROM pg_stat_activity a
                WHERE cardinality(pg_blocking_pids(a.pid)) > 0
                ORDER BY a.query_start
                """,
            )
            for row in blocking:
                row["blocked_query"] = _redact_query(row.get("blocked_query"))
            long_running = _rows(
                connection,
                """
                SELECT pid, usename, state,
                       now() - xact_start AS transaction_age,
                       left(query, 180) AS query
                FROM pg_stat_activity
                WHERE xact_start IS NOT NULL
                  AND now() - xact_start > interval '5 minutes'
                ORDER BY xact_start
                LIMIT 20
                """,
            )
            for row in long_running:
                row["query"] = _redact_query(row.get("query"))
            result["locks"] = {
                "status": "AVAILABLE",
                "blocking_detected": bool(blocking),
                "blocked_queries": blocking,
                "long_running_transactions": long_running,
                "active_transactions": _scalar(
                    connection,
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'",
                    None,
                ),
            }

            total_indexes = _scalar(
                connection,
                "SELECT count(*) FROM pg_stat_user_indexes",
                None,
            )
            unused_count = _scalar(
                connection,
                """
                SELECT count(*)
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                """,
                None,
            )
            index_rows = _rows(
                connection,
                """
                SELECT schemaname, relname AS table_name,
                       indexrelname AS index_name,
                       idx_scan,
                       pg_relation_size(indexrelid) AS size_bytes
                FROM pg_stat_user_indexes
                ORDER BY pg_relation_size(indexrelid) DESC
                LIMIT 25
                """,
            )
            invalid_count = _scalar(
                connection,
                """
                SELECT count(*)
                FROM pg_index
                WHERE NOT indisvalid
                """,
                None,
            )
            if total_indexes is not None:
                result["indexes"] = {
                    "status": "AVAILABLE",
                    "total_indexes": total_indexes,
                    "unused_indexes": [
                        row for row in index_rows if (row.get("idx_scan") or 0) == 0
                    ],
                    "unused_index_count": unused_count,
                    "invalid_indexes": invalid_count,
                    "largest_indexes": index_rows,
                }

            maintenance = _rows(
                connection,
                """
                SELECT schemaname, relname AS table_name,
                       n_live_tup, n_dead_tup,
                       last_vacuum, last_autovacuum,
                       last_analyze, last_autoanalyze
                FROM pg_stat_user_tables
                ORDER BY n_dead_tup DESC
                LIMIT 50
                """,
            )
            dead_tuple_tables = _scalar(
                connection,
                """
                SELECT count(*)
                FROM pg_stat_user_tables
                WHERE n_dead_tup > 0
                """,
                None,
            )
            result["maintenance"] = {
                "status": "AVAILABLE",
                "tables": maintenance,
                "tables_with_dead_tuples": dead_tuple_tables,
                "autovacuum": _setting(connection, "autovacuum"),
                "track_counts": _setting(connection, "track_counts"),
            }

            archive_mode = _setting(connection, "archive_mode")
            wal_level = _setting(connection, "wal_level")
            replica_count = _scalar(
                connection,
                "SELECT count(*) FROM pg_stat_replication",
                None,
            )
            result["backup_recovery"] = {
                "backup_integration": "NOT_CONFIGURED",
                "last_backup": None,
                "backup_status": "UNKNOWN",
                "restore_verification": "NOT_AVAILABLE",
                "point_in_time_recovery": (
                    "ENABLED_BUT_UNVERIFIED"
                    if archive_mode == "on"
                    else "NOT_CONFIRMED"
                ),
                "archive_mode": archive_mode,
                "wal_level": wal_level,
            }
            result["replication"] = {
                "status": "AVAILABLE",
                "is_standby": _scalar(
                    connection,
                    "SELECT pg_is_in_recovery()",
                    None,
                ),
                "replica_count": replica_count,
                "wal_level": wal_level,
                "archive_mode": archive_mode,
            }

            fk_count = _scalar(
                connection,
                "SELECT count(*) FROM pg_constraint WHERE contype = 'f'",
                None,
            )
            check_count = _scalar(
                connection,
                "SELECT count(*) FROM pg_constraint WHERE contype = 'c'",
                None,
            )
            result["integrity"] = {
                "status": (
                    "AVAILABLE"
                    if fk_count is not None and check_count is not None
                    else "NOT_AVAILABLE"
                ),
                "foreign_key_constraints": fk_count,
                "check_constraints": check_count,
                "application_integrity_checks": "NOT_CONFIGURED",
            }

            role = _scalar(connection, "SELECT current_user", None)
            role_row = _rows(
                connection,
                """
                SELECT rolname, rolsuper, rolcreaterole,
                       rolcreatedb, rolcanlogin
                FROM pg_roles
                WHERE rolname = current_user
                """,
            )
            role_info = role_row[0] if role_row else {}
            result["security"] = {
                "status": "AVAILABLE" if role else "NOT_AVAILABLE",
                "current_role": role,
                "ssl_enabled": _scalar(
                    connection,
                    """
                    SELECT ssl
                    FROM pg_stat_ssl
                    WHERE pid = pg_backend_pid()
                    """,
                    None,
                ),
                "is_superuser": role_info.get("rolsuper"),
                "can_create_role": role_info.get("rolcreaterole"),
                "can_create_database": role_info.get("rolcreatedb"),
                "can_login": role_info.get("rolcanlogin"),
                "pg_hba_analysis": "NOT_AVAILABLE_FROM_APPLICATION_ROLE",
            }

            result["recent_activity"] = _rows(
                connection,
                """
                SELECT pid, usename, state,
                       query_start,
                       wait_event_type,
                       wait_event,
                       left(query, 180) AS query
                FROM pg_stat_activity
                WHERE pid <> pg_backend_pid()
                  AND query IS NOT NULL
                  AND query <> '<IDLE>'
                ORDER BY query_start DESC NULLS LAST
                LIMIT 20
                """,
            )
            for row in result["recent_activity"]:
                row["query"] = _redact_query(row.get("query"))
    except Exception as exc:
        result["error"] = _safe_error(exc)

    return result


def inspect_schema(
    engine: Any,
    metadata: Any,
    *,
    checked_at: datetime,
) -> dict[str, Any]:
    if not metadata.tables:
        return {
            "state": "UNKNOWN",
            "tables_inspected": 0,
            "tables_with_drift": 0,
            "differences": [],
            "checked_at": checked_at.isoformat(),
            "error": "SQLAlchemy metadata is empty. Ensure application models are registered before diagnostics.",
        }

    differences: list[dict[str, Any]] = []
    inspector = inspect(engine)

    schemas = {table.schema for table in metadata.tables.values()}
    actual_tables: set[tuple[str | None, str]] = set()
    for schema in schemas:
        try:
            for table_name in inspector.get_table_names(schema=schema):
                actual_tables.add((schema, table_name))
        except Exception:
            continue

    for table_name, table in metadata.tables.items():
        key = (table.schema, table_name)
        if key not in actual_tables:
            differences.append(
                {
                    "table": table_name,
                    "schema": table.schema,
                    "kind": "missing-table",
                    "name": table_name,
                    "expected": "table",
                    "actual": None,
                }
            )
            continue

        try:
            actual_columns = {
                column["name"]: column
                for column in inspector.get_columns(
                    table_name,
                    schema=table.schema,
                )
            }
        except Exception as exc:
            differences.append(
                {
                    "table": table_name,
                    "schema": table.schema,
                    "kind": "table-inspection-error",
                    "name": table_name,
                    "expected": "readable",
                    "actual": f"{type(exc).__name__}: inspection failed",
                }
            )
            continue

        expected_columns = {column.name: column for column in table.columns}
        for name, column in expected_columns.items():
            if name not in actual_columns:
                differences.append(
                    {
                        "table": table_name,
                        "schema": table.schema,
                        "kind": "missing-column",
                        "name": name,
                        "expected": str(column.type),
                        "actual": None,
                    }
                )
        for name, column in actual_columns.items():
            if name not in expected_columns:
                differences.append(
                    {
                        "table": table_name,
                        "schema": table.schema,
                        "kind": "unexpected-column",
                        "name": name,
                        "expected": None,
                        "actual": str(column["type"]),
                    }
                )
        for name in expected_columns.keys() & actual_columns.keys():
            expected = expected_columns[name]
            actual = actual_columns[name]
            if str(expected.type).lower() != str(actual["type"]).lower():
                differences.append(
                    {
                        "table": table_name,
                        "schema": table.schema,
                        "kind": "column-type",
                        "name": name,
                        "expected": str(expected.type),
                        "actual": str(actual["type"]),
                    }
                )
            if bool(expected.nullable) != bool(actual["nullable"]):
                differences.append(
                    {
                        "table": table_name,
                        "schema": table.schema,
                        "kind": "column-nullability",
                        "name": name,
                        "expected": str(expected.nullable),
                        "actual": str(actual["nullable"]),
                    }
                )

    drift_tables = {
        (item.get("schema"), item["table"])
        for item in differences
    }
    return {
        "state": "DRIFT_DETECTED" if differences else "IN_SYNC",
        "tables_inspected": len(metadata.tables),
        "tables_with_drift": len(drift_tables),
        "differences": differences,
        "checked_at": checked_at.isoformat(),
        "error": None,
    }
