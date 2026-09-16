"""
EasyChatBot API Application.

Hosts the user interaction layer.

The API application is responsible only for:

- creating the FastAPI application;
- registering API routes;
- exposing the application health endpoint;
- triggering application composition bootstrap during startup;
- allowing the local frontend to communicate with the API.

Business logic belongs to application services.

Agent execution belongs to the agent/runtime layer.

Provider construction belongs to the composition layer.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.character_theme_routes import (
    router as character_theme_router,
)
from api.character_routes import (
    router as character_router,
)
from api.cinema_agent import (
    router as cinema_router,
)

from application.bootstrap import (
    bootstrap_application,
)

from application.telegram_bootstrap import (
    start_telegram_runtime,
    stop_telegram_runtime,
)

from app.application.provider_management.functionality_control_composition import (
    create_standalone_functionality_control_service,
)

from app.interfaces.provider_management.operations_center_dashboard_router import (
    router as operations_center_dashboard_router,
)

from app.api.cybersecurity_intelligence import (
    router as cybersecurity_intelligence_router,
)


@asynccontextmanager
async def lifespan(
    application: FastAPI,
):
    """
    Manage application startup and shutdown lifecycle.

    Startup:
        - compose application dependencies;
        - create the authoritative functionality-control service;
        - start Telegram transport runtime.

    Shutdown:
        - stop Telegram transport runtime;
        - dispose of the functionality-control database engine.

    This layer does not:

    - execute agents;
    - execute capabilities;
    - create providers;
    - create Runtime components.
    """

    bootstrap_application()

    (
        functionality_control_service,
        functionality_control_engine,
    ) = create_standalone_functionality_control_service()

    application.state.functionality_control_service = (
        functionality_control_service
    )
    application.state.functionality_control_engine = (
        functionality_control_engine
    )

    try:
        await start_telegram_runtime(
            functionality_control_service=(
                functionality_control_service
            ),
        )

        yield

    finally:
        await stop_telegram_runtime()

        functionality_control_engine.dispose()

        application.state.functionality_control_service = None
        application.state.functionality_control_engine = None


def create_app() -> FastAPI:
    """
    Create the EasyChatBot FastAPI application.

    Application composition is intentionally separated
    from the HTTP layer.

    This function:

    - creates the FastAPI application;
    - configures local frontend access;
    - registers API routes;
    - attaches lifecycle management.

    It does not:

    - execute agents;
    - execute capabilities;
    - call providers directly;
    - create Runtime executors.
    """

    application = FastAPI(
        title="EasyChatBot",
        description="AI companion learning platform",
        lifespan=lifespan,
    )

    # =========================================================
    # Local Frontend CORS
    # =========================================================

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:5500",
            "http://localhost:5500",
            "http://127.0.0.1:5501",
            "http://localhost:5501",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # =========================================================
    # Existing API Routes
    # =========================================================

    application.include_router(
        router,
    )

    # =========================================================
    # Agentic Cinema Routes
    # =========================================================
    #
    # Browser
    #     ↓
    # /api/cinema
    #     ↓
    # FastAPI Cinema Boundary
    #     ↓
    # Google Agent Runtime
    #     ↓
    # Gemini + Parallel + G5 workflow
    #
    # The API layer does not execute the agent directly.
    # The Cinema router owns the HTTP/application boundary.
    # =========================================================

    application.include_router(
        cinema_router,
    )

    # =========================================================
    # Character Theme Routes
    # =========================================================

    application.include_router(
        character_theme_router,
    )

    # =========================================================
    # Character Catalogue Routes
    # =========================================================

    application.include_router(
        character_router,
    )

    # =========================================================
    # AI Operations Center Routes
    # =========================================================

    application.include_router(
        operations_center_dashboard_router,
    )

    # =========================================================
    # Cybersecurity Intelligence Routes
    # =========================================================

    application.include_router(
        cybersecurity_intelligence_router,
    )

    return application


app = create_app()


@app.get("/")
def health() -> dict[str, str]:
    """
    Return application health status.
    """

    return {
        "status": "EasyChatBot running",
        "architecture": (
            "Runtime + Agents + Memory"
        ),
    }
