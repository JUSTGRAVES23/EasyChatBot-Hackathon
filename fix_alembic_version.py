from __future__ import annotations

from dotenv import load_dotenv
from sqlalchemy import text

from backend.app.infrastructure.persistence.database import (
    create_database_engine,
)


load_dotenv()


def main() -> None:

    engine = create_database_engine()

    with engine.connect() as conn:

        conn.execute(
            text(
                """
                ALTER TABLE alembic_version
                ALTER COLUMN version_num TYPE VARCHAR(255)
                """
            )
        )

        conn.commit()

    print(
        "Alembic version column expanded successfully."
    )


if __name__ == "__main__":
    main()