from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import text

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPOSITORY_ROOT / "backend"

sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(REPOSITORY_ROOT / ".env")

from app.application.developer_admin.developer_admin_audit import (
    DeveloperAdminAuditService,
)
from app.infrastructure.developer_admin.postgresql_developer_admin_audit_repository import (
    PostgreSQLDeveloperAdminAuditRepository,
)
from app.infrastructure.persistence.database import (
    create_async_database_engine,
    create_async_session_factory,
)


DEVELOPER_ADMIN_ROLE = "developer_admin"
MUTATION_LOCK_KEY = 84172931


class BootstrapError(RuntimeError):
    """Controlled Developer Admin bootstrap failure."""


async def bootstrap_developer_admin(user_id: UUID) -> None:
    engine = create_async_database_engine()
    session_factory = create_async_session_factory(engine)

    audit_repository = PostgreSQLDeveloperAdminAuditRepository(session_factory)
    audit_service = DeveloperAdminAuditService(audit_repository)

    try:
        async with session_factory() as session:
            async with session.begin():

                await session.execute(
                    text("SELECT pg_advisory_xact_lock(:lock_key)"),
                    {"lock_key": MUTATION_LOCK_KEY},
                )

                user_result = await session.execute(
                    text(
                        """
                        SELECT
                            id,
                            email,
                            username,
                            status,
                            email_verified
                        FROM users
                        WHERE id = :user_id
                        FOR UPDATE
                        """
                    ),
                    {"user_id": user_id},
                )

                user = user_result.mappings().one_or_none()

                if user is None:
                    raise BootstrapError(
                        f"Target user does not exist: {user_id}"
                    )

                if str(user["status"]).lower() != "active":
                    raise BootstrapError(
                        "Target user must be active."
                    )

                if not user["email_verified"]:
                    raise BootstrapError(
                        "Target user must have a verified email address."
                    )

                existing_admin_result = await session.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM auth_user_roles
                        WHERE role = :role
                        """
                    ),
                    {"role": DEVELOPER_ADMIN_ROLE},
                )

                existing_admin_count = int(
                    existing_admin_result.scalar_one()
                )

                if existing_admin_count > 0:
                    raise BootstrapError(
                        "Developer Admin bootstrap refused: "
                        f"{existing_admin_count} Developer Administrator(s) "
                        "already exist."
                    )

                role_result = await session.execute(
                    text(
                        """
                        INSERT INTO auth_user_roles (user_id, role)
                        VALUES (:user_id, :role)
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {
                        "user_id": user_id,
                        "role": DEVELOPER_ADMIN_ROLE,
                    },
                )

                if role_result.rowcount != 1:
                    raise BootstrapError(
                        "Developer Admin role was not created."
                    )

                audit_event = await audit_service.build_bootstrap_event(
                    target_user_id=user["id"],
                    target_email=user["email"],
                )

                await audit_repository.record_in_session(
                    session,
                    audit_event,
                )

                print("BOOTSTRAP SUCCESS")
                print(f"User ID: {user['id']}")
                print(f"Username: {user['username']}")
                print(f"Email: {user['email']}")
                print("Status: active")
                print("Email verified: True")
                print("Role granted: developer_admin")
                print(f"Audit event: {audit_event.event_id}")
                print(f"Audit type: {audit_event.event_type}")
                print(f"Actor type: {audit_event.actor_type}")

    finally:
        await engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Controlled one-time bootstrap of the first "
            "EasyChatBot Developer Administrator."
        )
    )

    parser.add_argument(
        "user_id",
        type=UUID,
        help="UUID of the active, email-verified user to bootstrap.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        asyncio.run(
            bootstrap_developer_admin(args.user_id)
        )

    except BootstrapError as exc:
        print(
            f"BOOTSTRAP REFUSED: {exc}",
            file=sys.stderr,
        )
        return 2

    except Exception as exc:
        print(
            f"BOOTSTRAP FAILED: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
