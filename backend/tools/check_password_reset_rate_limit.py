from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

# Load the EasyChatBot-Hackathon root .env
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

from app.infrastructure.persistence.database import (  # noqa: E402
    create_async_database_engine,
    create_async_session_factory,
)


EMAIL = "davdbarbero1999@gmail.com"


async def main() -> None:
    engine = create_async_database_engine()
    session_factory = create_async_session_factory(engine)

    try:
        async with session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT
                        u.id,
                        u.email,
                        COUNT(t.id) AS reset_requests_last_hour
                    FROM users u
                    LEFT JOIN auth_password_reset_tokens t
                        ON t.user_id = u.id
                       AND t.created_at >= :since
                    WHERE lower(u.email) = lower(:email)
                    GROUP BY u.id, u.email
                    """
                ),
                {
                    "since": (
                        datetime.now(timezone.utc)
                        - timedelta(hours=1)
                    ),
                    "email": EMAIL,
                },
            )

            rows = result.mappings().all()

            print()
            print("Password-reset rate-limit diagnostic")
            print("------------------------------------")

            if not rows:
                print("NO USER FOUND")
                return

            for row in rows:
                print(f"User ID: {row['id']}")
                print(f"Email: {row['email']}")
                print(
                    "Reset requests in last hour: "
                    f"{row['reset_requests_last_hour']}"
                )

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())