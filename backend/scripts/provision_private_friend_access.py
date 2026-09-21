from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(r"C:\AI Folder\EasyChatBot-Hackathon")
BACKEND_ROOT = PROJECT_ROOT / "backend"

load_dotenv(PROJECT_ROOT / ".env")

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from app.application.beta_access.beta_access_service import BetaAccessService
from app.application.beta_access.models import BetaUserState
from app.application.uai.world.world_resolver import WorldResolver
from app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.postgresql_beta_access_repository import (
    PostgreSQLBetaTokenRepository,
    PostgreSQLBetaUserRepository,
    PostgreSQLTelegramBindingRepository,
)
from app.infrastructure.worlds.yaml_world_repository import YamlWorldRepository


USERS = [
    {
        "user": BetaUserState(
            user_id="omayma",
            email="omayma.tilani@gmail.com",
            email_verified=True,
            beta_approved=False,
            active_world_id=None,
        ),
        "world_id": "luxembourgish_world",
        "label": "Luxembourgish",
    },
    {
        "user": BetaUserState(
            user_id="sergio",
            email="sergio.barbero.bascones95@gmail.com",
            email_verified=True,
            beta_approved=False,
            active_world_id=None,
        ),
        "world_id": "polish_world",
        "label": "Polish",
    },
]


def create_beta_access_service() -> BetaAccessService:
    engine = create_database_engine()
    session_factory = create_session_factory(engine)

    world_repository = YamlWorldRepository(
        worlds_path=BACKEND_ROOT / "app" / "configuration" / "worlds",
    )

    world_resolver = WorldResolver(
        world_repository=world_repository,
    )

    return BetaAccessService(
        user_repository=PostgreSQLBetaUserRepository(session_factory),
        token_repository=PostgreSQLBetaTokenRepository(session_factory),
        binding_repository=PostgreSQLTelegramBindingRepository(session_factory),
        world_resolver=world_resolver,
    )


async def provision() -> None:
    service = create_beta_access_service()

    bot_username = os.getenv("TELEGRAM_BOT_USERNAME")

    if not bot_username:
        raise RuntimeError(
            "TELEGRAM_BOT_USERNAME is required in the project .env file."
        )

    bot_username = bot_username.lstrip("@")

    output_lines = []

    for item in USERS:
        user = item["user"]
        world_id = item["world_id"]
        label = item["label"]

        print("")
        print("=" * 70)
        print(f"Provisioning: {user.user_id}")
        print(f"Email:        {user.email}")
        print(f"World:        {label} ({world_id})")
        print("=" * 70)

        # Persist learner identity.
        await service._users.save(user)

        # Approve Beta access.
        await service.approve_beta(user.user_id)

        # Assign the requested Learning World.
        await service.assign_world(
            user_id=user.user_id,
            world_id=world_id,
        )

        # Generate a real one-time Telegram connection token.
        token_result = await service.create_connection_token(
            user.user_id,
        )

        telegram_url = (
            f"https://t.me/"
            f"{bot_username}"
            f"?start={token_result.token}"
        )

        output_lines.extend(
            [
                "",
                f"User: {user.user_id}",
                f"Email: {user.email}",
                f"World: {label}",
                f"World ID: {world_id}",
                f"Telegram invitation: {telegram_url}",
                "",
            ]
        )

        print("")
        print(f"USER:      {user.user_id}")
        print(f"EMAIL:     {user.email}")
        print(f"WORLD:     {label}")
        print(f"WORLD ID:  {world_id}")
        print("")
        print("TELEGRAM INVITATION:")
        print(telegram_url)
        print("")

    output_path = PROJECT_ROOT / "PRIVATE_TELEGRAM_INVITATIONS.txt"
    output_path.write_text(
        "\n".join(output_lines),
        encoding="utf-8",
    )

    print("=" * 70)
    print("PROVISIONING COMPLETE")
    print("=" * 70)
    print(f"Invitation file: {output_path}")

    print("")
    print("IMPORTANT:")
    print("Each Telegram invitation contains a one-time connection token.")
    print("Send each invitation only to its intended person.")
    print("")


if __name__ == "__main__":
    asyncio.run(provision())
