from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

from app.infrastructure.persistence.database import (  # noqa: E402
    create_async_database_engine,
    create_async_session_factory,
)


USER_ID = "04ad330b-f0f0-4743-af6c-bd0d7da7f255"


async def main() -> None:
    engine = create_async_database_engine()
    session_factory = create_async_session_factory(engine)

    try:
        async with session_factory() as session:
            since = datetime.now(timezone.utc) - timedelta(hours=1)

            result = await session.execute(
                text(
                    """
                    DELETE FROM auth_password_reset_tokens
                    WHERE user_id = :user_id
                      AND created_at >= :since
                    """
                ),
                {
                    "user_id": USER_ID,
                    "since": since,
                },
            )

            deleted = result.rowcount

            await session.commit()

            print()
            print("Password-reset test cleanup")
            print("---------------------------")
            print(f"User ID: {USER_ID}")
            print(f"Records deleted: {deleted}")
            print("Transaction committed.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())