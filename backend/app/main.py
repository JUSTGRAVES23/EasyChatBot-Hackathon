"""
EasyChatBot FastAPI Application.

Application entry point.

Responsibilities:
- Create FastAPI application.
- Register API routers.
- Configure application metadata.

Does NOT:
- Execute AI agents.
- Handle business logic.
- Manage voice sessions.
- Call external providers.
"""

from __future__ import annotations


from fastapi import FastAPI


from fastapi.middleware.cors import CORSMiddleware



from app.api.voice_calls import (
    router as voice_calls_router,
)


from app.api.voice_reconnect_router import (
    router as voice_reconnect_router,
)


from app.api.voice_call_trigger import (
    router as voice_call_trigger_router,
)


from app.api.voice_notification_acceptance import (
    router as voice_notification_acceptance_router,
)


from app.api.operations_center import (
    router as operations_center_router,
)



def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    """


    application = FastAPI(
        title="EasyChatBot API",
        description=(
            "AI character learning platform API"
        ),
        version="0.1.0",
    )


    #
    # CORS
    #
    # Allows Next.js frontend
    # to consume backend APIs.
    #

    application.add_middleware(
        CORSMiddleware,

        allow_origins=[
            "http://localhost:3000",
        ],

        allow_credentials=True,

        allow_methods=[
            "*",
        ],

        allow_headers=[
            "*",
        ],
    )



    #
    # Voice Calls API
    #

    application.include_router(
        voice_calls_router
    )



    #
    # Voice Reconnect API
    #

    application.include_router(
        voice_reconnect_router
    )



    #
    # Voice Trigger API
    #
    # Starts:
    #
    # VoiceCall
    #      |
    #      ↓
    # Invitation
    #      |
    #      ↓
    # Notification
    #

    application.include_router(
        voice_call_trigger_router
    )



    #
    # Voice Notification Acceptance API
    #
    # Flow:
    #
    # Notification Inbox
    #        |
    #        ↓
    # Accept
    #        |
    #        ↓
    # VoiceCallSession
    #

    application.include_router(
        voice_notification_acceptance_router
    )



    #
    # AI Operations Center API
    #

    application.include_router(
        operations_center_router
    )


    return application



app = create_application()