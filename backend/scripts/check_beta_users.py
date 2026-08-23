from __future__ import annotations

import os

from sqlalchemy import create_engine, text


engine = create_engine(
    os.environ["DATABASE_URL"]
)


with engine.connect() as conn:

    print("\nBETA USERS")

    rows = conn.execute(
        text(
            """
            SELECT
                id,
                email,
                approved,
                active_world_id,
                telegram_id
            FROM beta_users
            """
        )
    )

    for row in rows:
        print(row)


    print("\nTOKENS")

    rows = conn.execute(
        text(
            """
            SELECT
                id,
                user_id,
                expires_at,
                used_at
            FROM beta_connection_tokens
            """
        )
    )

    for row in rows:
        print(row)


    print("\nBINDINGS")

    rows = conn.execute(
        text(
            """
            SELECT
                user_id,
                telegram_user_id,
                chat_id
            FROM telegram_bindings
            """
        )
    )

    for row in rows:
        print(row)