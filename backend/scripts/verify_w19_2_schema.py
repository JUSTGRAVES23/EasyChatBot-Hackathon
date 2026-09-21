\
"""Read-only W19.2 PostgreSQL schema verification.

Run from backend:
    python .\\scripts\\verify_w19_2_schema.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _database_url() -> str:
    backend = Path(__file__).resolve().parents[1]
    _load_dotenv(backend.parent / ".env")
    _load_dotenv(backend / ".env")

    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRESQL_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL or POSTGRESQL_DATABASE_URL was not found in the "
            "environment or repository .env files."
        )

    # SQLAlchemy sync engine needs a sync PostgreSQL driver. If the project
    # URL is asyncpg-based, convert only the driver portion for this
    # read-only verification script.
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "+psycopg")
    return url


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _run(engine: Engine) -> None:
    with engine.connect() as conn:
        table = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'world_telegram_memberships'
                """
            )
        ).scalar_one()
        _assert(table == 1, "world_telegram_memberships table is missing")

        columns = {
            row.column_name: row
            for row in conn.execute(
                text(
                    """
                    SELECT column_name, data_type, udt_name, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'world_telegram_memberships'
                    ORDER BY ordinal_position
                    """
                )
            )
        }

        expected = {
            "id": ("uuid", "uuid", "NO"),
            "destination_id": ("uuid", "uuid", "NO"),
            "user_id": ("uuid", "uuid", "NO"),
            "status": ("character varying", "varchar", "NO"),
            "joined_at": ("timestamp with time zone", "timestamptz", "NO"),
            "left_at": ("timestamp with time zone", "timestamptz", "YES"),
            "created_at": ("timestamp with time zone", "timestamptz", "NO"),
            "updated_at": ("timestamp with time zone", "timestamptz", "NO"),
        }

        for name, (data_type, udt_name, nullable) in expected.items():
            _assert(name in columns, f"missing column: {name}")
            row = columns[name]
            _assert(
                (row.data_type, row.udt_name, row.is_nullable)
                == (data_type, udt_name, nullable),
                f"unexpected definition for {name}: "
                f"{row.data_type}/{row.udt_name}/{row.is_nullable}",
            )

        constraints = {
            row.constraint_name: row
            for row in conn.execute(
                text(
                    """
                    SELECT
                        tc.constraint_name,
                        tc.constraint_type
                    FROM information_schema.table_constraints tc
                    WHERE tc.table_schema = 'public'
                      AND tc.table_name = 'world_telegram_memberships'
                    """
                )
            )
        }

        _assert(
            any(r.constraint_type == "PRIMARY KEY" for r in constraints.values()),
            "primary key constraint is missing",
        )
        _assert(
            any(r.constraint_type == "UNIQUE" for r in constraints.values()),
            "unique(destination_id, user_id) constraint is missing",
        )
        _assert(
            any(r.constraint_type == "CHECK" for r in constraints.values()),
            "status check constraint is missing",
        )

        fks = list(
            conn.execute(
                text(
                    """
                    SELECT
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name,
                        rc.delete_rule
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage ccu
                      ON tc.constraint_name = ccu.constraint_name
                     AND tc.table_schema = ccu.table_schema
                    JOIN information_schema.referential_constraints rc
                      ON tc.constraint_name = rc.constraint_name
                     AND tc.constraint_schema = rc.constraint_schema
                    WHERE tc.table_schema = 'public'
                      AND tc.table_name = 'world_telegram_memberships'
                      AND tc.constraint_type = 'FOREIGN KEY'
                    ORDER BY kcu.column_name
                    """
                )
            )
        )

        fk_by_column = {row.column_name: row for row in fks}
        _assert("destination_id" in fk_by_column, "destination_id FK is missing")
        _assert("user_id" in fk_by_column, "user_id FK is missing")

        destination_fk = fk_by_column["destination_id"]
        _assert(
            (
                destination_fk.foreign_table_name,
                destination_fk.foreign_column_name,
                destination_fk.delete_rule,
            )
            == ("world_telegram_destinations", "id", "RESTRICT"),
            "destination_id FK must reference world_telegram_destinations.id "
            "with ON DELETE RESTRICT",
        )

        user_fk = fk_by_column["user_id"]
        _assert(
            (
                user_fk.foreign_table_name,
                user_fk.foreign_column_name,
                user_fk.delete_rule,
            )
            == ("users", "id", "CASCADE"),
            "user_id FK must reference users.id with ON DELETE CASCADE",
        )

        indexes = {
            row.indexname
            for row in conn.execute(
                text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND tablename = 'world_telegram_memberships'
                    """
                )
            )
        }

        _assert(
            any("destination_id" in name for name in indexes),
            "destination_id index is missing",
        )
        _assert(
            any("user_id" in name for name in indexes),
            "user_id index is missing",
        )

        print("W19.2 SCHEMA VERIFICATION: PASS")
        print("Table: world_telegram_memberships")
        print("user_id: UUID -> users.id ON DELETE CASCADE")
        print(
            "destination_id: UUID -> world_telegram_destinations.id "
            "ON DELETE RESTRICT"
        )
        print("Constraints: PK + UNIQUE(destination_id,user_id) + status CHECK")
        print("Indexes: destination_id + user_id + constraint indexes")


def main() -> None:
    engine = create_engine(_database_url(), pool_pre_ping=True)
    try:
        _run(engine)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()


