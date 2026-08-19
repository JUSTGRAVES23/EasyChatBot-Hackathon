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

from backend.api.routes import router
from backend.api.character_theme_routes import (
    router as character_theme_router,
)
from backend.api.character_routes import (
    router as character_router,
)
from backend.application.bootstrap import bootstrap_application

from app.interfaces.provider_management.operations_center_dashboard_router import (
    router as operations_center_dashboard_router,
)


@asynccontextmanager
async def lifespan(
    application: FastAPI,
):
    """
    Manage application startup and shutdown lifecycle.

    Startup:
        bootstrap application dependencies.

    Shutdown:
        reserved for future controlled cleanup.

    This layer does not:

    - execute agents;
    - execute capabilities;
    - create providers;
    - create Runtime components.
    """

    bootstrap_application()

    yield


def create_app() -> FastAPI:
    """
    Create the EasyChatBot FastAPI application.

    Application composition is intentionally separated
    from the HTTP layer.

    This function:

    - creates the application object;
    - configures local frontend access;
    - registers routes;
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
    #
    # Read-only Operations Center boundary.
    #
    # Exposes:
    #
    #     GET /api/operations-center/dashboard
    #     GET /api/operations-center/operational-events
    #
    # The router delegates to the already-composed application
    # services. The FastAPI bootstrap does not create providers,
    # Runtime components, repositories, or operational events.

    application.include_router(
        operations_center_dashboard_router,
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

