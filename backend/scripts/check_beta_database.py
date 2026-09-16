from __future__ import annotations

import sys
from pathlib import Path


# =====================================================
# Python path bootstrap
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# =====================================================
# Load environment
# =====================================================

from dotenv import load_dotenv


load_dotenv(
    PROJECT_ROOT / ".env"
)


# =====================================================
# Imports
# =====================================================

from sqlalchemy import text

from app.infrastructure.persistence.database import (
    create_database_engine,
)


# =====================================================
# Database validation
# =====================================================


def main() -> None:

    engine = create_database_engine()


    # -------------------------------------------------
    # Database
    # -------------------------------------------------

    print("\nDatabase:")

    with engine.connect() as conn:

        print(
            conn.execute(
                text(
                    "SELECT current_database();"
                )
            ).fetchall()
        )


    # -------------------------------------------------
    # Alembic
    # -------------------------------------------------

    print("\nAlembic version:")

    with engine.connect() as conn:

        print(
            conn.execute(
                text(
                    """
                    SELECT version_num
                    FROM alembic_version;
                    """
                )
            ).fetchall()
        )


    # -------------------------------------------------
    # Beta users
    # -------------------------------------------------

    print("\nBeta users:")

    with engine.connect() as conn:

        print(
            conn.execute(
                text(
                    """
                    SELECT
                        id,
                        email,
                        approved,
                        email_verified,
                        active_world_id,
                        telegram_id
                    FROM beta_users;
                    """
                )
            ).fetchall()
        )


    # -------------------------------------------------
    # Telegram bindings
    # -------------------------------------------------

    print("\nTelegram bindings:")

    with engine.connect() as conn:

        print(
            conn.execute(
                text(
                    """
                    SELECT
                        id,
                        user_id,
                        telegram_user_id,
                        chat_id
                    FROM telegram_bindings;
                    """
                )
            ).fetchall()
        )


    # -------------------------------------------------
    # Beta tokens
    # -------------------------------------------------

    print("\nBeta connection tokens:")

    with engine.connect() as conn:

        print(
            conn.execute(
                text(
                    """
                    SELECT
                        id,
                        user_id,
                        expires_at,
                        used_at
                    FROM beta_connection_tokens;
                    """
                )
            ).fetchall()
        )


    # -------------------------------------------------
    # Conversation events
    # -------------------------------------------------

    print("\nConversation events:")

    with engine.connect() as conn:

        try:

            rows = conn.execute(
                text(
                    """
                    SELECT
                        id,
                        conversation_id,
                        telegram_user_hash,
                        world_id,
                        channel,
                        role,
                        content,
                        metadata_json,
                        created_at
                    FROM conversation_events
                    ORDER BY created_at DESC
                    LIMIT 20;
                    """
                )
            ).fetchall()


            for row in rows:
                print(row)


        except Exception as exc:

            print(
                "Conversation events table unavailable:"
            )

            print(exc)



if __name__ == "__main__":
    main()
