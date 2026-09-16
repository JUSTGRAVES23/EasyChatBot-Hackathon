from __future__ import annotations

import logging

from app.application.composition.beta_telegram_production import (
    BetaTelegramProductionComposition,
    create_production_beta_telegram_composition,
)
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)
from app.application.composition.conversation_composition import (
    create_conversation_runtime,
)
from app.application.uai.language.language_detector import (
    LanguageDetector,
)
from app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.telegram.telegram_bot_runtime import (
    TelegramBotRuntime,
)


logger = logging.getLogger(__name__)


_telegram_production: (
    BetaTelegramProductionComposition | None
) = None


def create_telegram_runtime(
    *,
    functionality_control_service: FunctionalityOperationalControlService,
    language_detector: LanguageDetector,
) -> TelegramBotRuntime:
    """
    Create the production Beta Telegram runtime.

    The functionality-control service and language detector are supplied
    explicitly by the application composition. Telegram bootstrap does not
    create a second control repository or control service, and it does not
    create a default language detector.
    """

    global _telegram_production

    if functionality_control_service is None:
        raise ValueError(
            "functionality_control_service is required."
        )

    if language_detector is None:
        raise ValueError(
            "language_detector is required."
        )

    if _telegram_production is None:
        _telegram_production = (
            create_production_beta_telegram_composition(
                database_engine_factory=(
                    create_database_engine
                ),
                session_factory_factory=(
                    create_session_factory
                ),
                conversation_runtime_factory=(
                    create_conversation_runtime
                ),
                functionality_control_service=(
                    functionality_control_service
                ),
                language_detector=language_detector,
            )
        )

        logger.info(
            "Production Beta Telegram composition created."
        )

    return _telegram_production.beta_telegram.runtime


async def start_telegram_runtime(
    *,
    functionality_control_service: FunctionalityOperationalControlService,
    language_detector: LanguageDetector,
) -> None:
    """
    Start the production Telegram runtime.
    """

    runtime = create_telegram_runtime(
        functionality_control_service=(
            functionality_control_service
        ),
        language_detector=language_detector,
    )

    await runtime.start()

    logger.info(
        "Production Beta Telegram runtime started."
    )


async def stop_telegram_runtime() -> None:
    """
    Stop the production Telegram runtime.
    """

    if _telegram_production is None:
        return

    await _telegram_production.beta_telegram.runtime.stop()

    logger.info(
        "Production Beta Telegram runtime stopped."
    )


def reset_telegram_runtime() -> None:
    """
    Reset the Telegram production composition.

    Intended primarily for tests and controlled lifecycle
    management.
    """

    global _telegram_production

    _telegram_production = None


def get_telegram_production_composition() -> (
    BetaTelegramProductionComposition
):
    """
    Return the active production Beta Telegram composition.
    """

    if _telegram_production is None:
        raise RuntimeError(
            "Telegram production composition has not been created."
        )

    return _telegram_production


__all__ = [
    "create_telegram_runtime",
    "start_telegram_runtime",
    "stop_telegram_runtime",
    "reset_telegram_runtime",
    "get_telegram_production_composition",
]