from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# Project paths
#
# Repository:
#
# EasyChatBot-Hackathon
#   |
#   ├── .env
#   └── backend
#       ├── app
#       └── scripts
#
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BACKEND_ROOT = PROJECT_ROOT / "backend"


# ============================================================
# Load application environment
#
# Same configuration source used by the application.
# ============================================================

load_dotenv(
    PROJECT_ROOT / ".env"
)


# ============================================================
# Python import path setup
#
# Existing backend modules use:
#
#     from backend.app....
#
# Therefore backend/ must be a Python root.
#
# ============================================================

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_ROOT),
    )


from backend.app.application.beta_access.beta_access_service import (
    BetaAccessService,
)

from backend.app.application.beta_access.models import (
    BetaUserState,
)

from backend.app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)

from backend.app.infrastructure.persistence.postgresql_beta_access_repository import (
    PostgreSQLBetaTokenRepository,
    PostgreSQLBetaUserRepository,
    PostgreSQLTelegramBindingRepository,
)


DEMO_USERS = [
    BetaUserState(
        user_id="david",
        email="david@example.com",
        email_verified=True,
        beta_approved=False,
        active_world_id=None,
    ),
    BetaUserState(
        user_id="brother",
        email="brother@example.com",
        email_verified=True,
        beta_approved=False,
        active_world_id=None,
    ),
]


def create_beta_access_service() -> BetaAccessService:
    """
    Create BetaAccessService using PostgreSQL persistence.
    """

    engine = create_database_engine()

    session_factory = create_session_factory(
        engine,
    )

    return BetaAccessService(
        user_repository=PostgreSQLBetaUserRepository(
            session_factory,
        ),
        token_repository=PostgreSQLBetaTokenRepository(
            session_factory,
        ),
        binding_repository=PostgreSQLTelegramBindingRepository(
            session_factory,
        ),
    )


async def provision_beta_users() -> None:
    """
    Provision Phase B.4 demo Beta users.

    Flow:

        Create Beta user
              |
              v
        Approve Beta access
              |
              v
        Assign Learning World
              |
              v
        Create Telegram token
              |
              v
        Generate Telegram deep link
    """

    service = create_beta_access_service()

    bot_username = os.getenv(
        "TELEGRAM_BOT_USERNAME",
    )

    if not bot_username:
        raise RuntimeError(
            "TELEGRAM_BOT_USERNAME is required."
        )

    bot_username = bot_username.lstrip("@")

    for user in DEMO_USERS:

        print(
            f"Provisioning {user.user_id}..."
        )

        #
        # Initial user persistence.
        #
        # Current BetaAccessService expects
        # an existing Academy user.
        #
        # Later improvement:
        # expose register_beta_user()
        # in BetaAccessService.
        #

        await service._users.save(
            user,
        )

        await service.approve_beta(
            user.user_id,
        )

        await service.assign_world(
            user_id=user.user_id,
            world_id="world-fr",
        )

        token_result = await service.create_connection_token(
            user.user_id,
        )

        telegram_url = (
            f"https://t.me/"
            f"{bot_username}"
            f"?start={token_result.token}"
        )

        print("")
        print("==============================")
        print(
            f"Beta User: {user.user_id}"
        )
        print(
            f"Email: {user.email}"
        )
        print(
            "World: world-fr"
        )
        print(
            "Telegram invitation:"
        )
        print(
            telegram_url
        )
        print("==============================")


if __name__ == "__main__":

    asyncio.run(
        provision_beta_users()
    )
