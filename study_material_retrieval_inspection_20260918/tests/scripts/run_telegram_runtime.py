from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# Environment
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(
    PROJECT_ROOT / ".env"
)


# ============================================================
# Python path
# ============================================================

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


from application.telegram_bootstrap import (
    start_telegram_runtime,
    stop_telegram_runtime,
)

from app.application.provider_management.functionality_control_composition import (
    create_standalone_functionality_control_service,
)


async def main():
    logging.info(
        "Starting EasyChatBot Telegram Beta runtime..."
    )

    (
        functionality_control_service,
        functionality_control_engine,
    ) = create_standalone_functionality_control_service()

    try:
        await start_telegram_runtime(
            functionality_control_service=(
                functionality_control_service
            ),
        )

        logging.info(
            "Telegram runtime is running."
        )

        while True:
            await asyncio.sleep(3600)

    except KeyboardInterrupt:
        logging.info(
            "Shutdown requested."
        )

    finally:
        await stop_telegram_runtime()

        functionality_control_engine.dispose()

        logging.info(
            "Telegram runtime stopped."
        )


if __name__ == "__main__":
    asyncio.run(
        main()
    )

