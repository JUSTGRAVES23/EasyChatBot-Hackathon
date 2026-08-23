from sqlalchemy import create_engine, text
import os


database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL is missing"
    )


engine = create_engine(database_url)


with engine.connect() as connection:

    print("Database:")
    print(
        connection.execute(
            text("SELECT current_database();")
        ).fetchone()
    )

    print("\nAlembic version:")
    print(
        connection.execute(
            text(
                "SELECT version_num FROM alembic_version;"
            )
        ).fetchall()
    )

    print("\nBeta tables:")

    print(
        connection.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name IN (
                    'beta_users',
                    'telegram_bindings',
                    'beta_connection_tokens'
                )
                ORDER BY table_name;
                """
            )
        ).fetchall()
    )