"""
EasyChatBot API Application.

Hosts the user interaction layer.

The API application is responsible only for:

- creating the FastAPI application;
- registering API routes;
- exposing the application health endpoint;
- triggering application composition bootstrap during startup.

Business logic belongs to application services.

Agent execution belongs to the agent/runtime layer.

Provider construction belongs to the composition layer.
"""

from __future__ import annotations


from contextlib import asynccontextmanager

from fastapi import FastAPI


from backend.api.routes import (
    router,
)

from backend.application.bootstrap import (
    bootstrap_application,
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


    application.include_router(
        router,
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