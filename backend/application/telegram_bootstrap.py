from __future__ import annotations


import logging


from backend.app.application.beta_access.beta_access_service import (
    BetaAccessService,
)


from backend.app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)


from backend.app.application.beta_access.telegram_conversation_service import (
    TelegramConversationService,
)


from backend.app.application.composition.conversation_composition import (
    create_conversation_runtime,
)


from backend.app.application.conversation_quality.conversation_event_validator import (
    ConversationEventValidator,
)


from backend.app.application.privacy.privacy_identifier_service import (
    PrivacyIdentifierService,
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


from backend.app.infrastructure.persistence.postgresql_conversation_event_repository import (
    PostgreSQLConversationEventRepository,
)


from backend.app.infrastructure.telegram.telegram_bot_runtime import (
    TelegramBotRuntime,
)


from backend.app.interfaces.telegram.beta_start_handler import (
    BetaTelegramStartHandler,
)


from backend.app.interfaces.telegram.beta_telegram_adapter import (
    BetaTelegramAdapter,
)


from backend.app.interfaces.telegram.private_chat_gate import (
    BetaPrivateChatGate,
)



logger = logging.getLogger(__name__)



_telegram_runtime: TelegramBotRuntime | None = None






def create_telegram_runtime() -> TelegramBotRuntime:
    """
    Compose Telegram Beta runtime.

    Composition layer only.

    Flow:

        Database
            |
            v
        Repositories
            |
            v
        Application Services
            |
            v
        Runtime

    """

    global _telegram_runtime


    if _telegram_runtime is not None:

        return _telegram_runtime




    # =================================================
    # Database
    # =================================================

    engine = create_database_engine()


    session_factory = create_session_factory(
        engine,
    )




    # =================================================
    # Beta access
    # =================================================

    beta_access_service = BetaAccessService(

        user_repository=(
            PostgreSQLBetaUserRepository(
                session_factory,
            )
        ),

        token_repository=(
            PostgreSQLBetaTokenRepository(
                session_factory,
            )
        ),

        binding_repository=(
            PostgreSQLTelegramBindingRepository(
                session_factory,
            )
        ),

    )





    # =================================================
    # Conversation quality governance
    #
    # Runs before persistence
    #
    # Checks:
    #
    # - no raw identity
    # - no personal context leakage
    # - metadata completeness
    # - retention classification
    #
    # =================================================

    conversation_event_validator = (
        ConversationEventValidator()
    )






    # =================================================
    # Conversation event repository
    #
    # Persistence ONLY
    #
    # No validation logic here
    #
    # =================================================

    conversation_event_repository = (
        PostgreSQLConversationEventRepository(

            session_factory,

        )
    )






    # =================================================
    # Privacy identifier
    #
    # Telegram ID
    #       |
    #       v
    # pseudonymous hash
    #
    # =================================================

    privacy_identifier_service = (
        PrivacyIdentifierService()
    )






    # =================================================
    # Private Telegram access gate
    # =================================================

    private_chat_gate = BetaPrivateChatGate(

        beta_access_service=beta_access_service,

    )






    # =================================================
    # Telegram start handler
    # =================================================

    async def telegram_reply(
        message,
        user,
    ):

        return message





    start_handler = BetaTelegramStartHandler(

        beta_access_service=beta_access_service,

        reply=telegram_reply,

    )






    # =================================================
    # AI runtime
    # =================================================

    conversation_runtime = (
        create_conversation_runtime()
    )






    # =================================================
    # Conversation application service
    #
    # Validator injected here
    #
    # =================================================

    conversation_service = TelegramConversationService(

        conversation_runtime=(
            conversation_runtime
        ),


        conversation_event_repository=(
            conversation_event_repository
        ),


        privacy_identifier_service=(
            privacy_identifier_service
        ),


        conversation_event_validator=(
            conversation_event_validator
        ),

    )






    # =================================================
    # Boundary
    # =================================================

    conversation_boundary = (
        BetaTelegramConversationBoundary(

            conversation_service=(
                conversation_service
            ),


            beta_access_service=(
                beta_access_service
            ),

        )
    )






    # =================================================
    # Telegram adapter
    # =================================================

    adapter = BetaTelegramAdapter(

        start_handler=start_handler,

        private_chat_gate=private_chat_gate,

    )






    # =================================================
    # Runtime
    # =================================================

    _telegram_runtime = TelegramBotRuntime(

        adapter=adapter,

        conversation_boundary=conversation_boundary,

    )





    logger.info(
        "Telegram runtime composed with PostgreSQL persistence, privacy layer, conversation validation and governance."
    )



    return _telegram_runtime






async def start_telegram_runtime() -> None:

    runtime = create_telegram_runtime()

    await runtime.start()






async def stop_telegram_runtime() -> None:

    if _telegram_runtime is None:

        return


    await _telegram_runtime.stop()






def reset_telegram_runtime() -> None:

    global _telegram_runtime

    _telegram_runtime = None