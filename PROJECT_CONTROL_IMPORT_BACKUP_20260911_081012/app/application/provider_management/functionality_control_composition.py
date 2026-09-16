from __future__ import annotations

from app.application.provider_management.functionality_control_authorizer import (
    AuthorizationFunctionalityControlAuthorizer,
)
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)
from app.infrastructure.persistence.postgresql_functionality_control_repository import (
    PostgreSQLFunctionalityControlRepository,
)
from app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)


def create_functionality_control_service(
    *,
    session_factory,
) -> FunctionalityOperationalControlService:
    """Create the approved functionality-control application service.

    The caller owns the database engine/session lifecycle.
    This helper only composes the application service boundary.
    """

    repository = PostgreSQLFunctionalityControlRepository(
        session_factory,
    )

    authorizer = AuthorizationFunctionalityControlAuthorizer()

    return FunctionalityOperationalControlService(
        authorizer=authorizer,
        repository=repository,
    )


def create_standalone_functionality_control_service() -> tuple[
    FunctionalityOperationalControlService,
    object,
]:
    """Create a control service for a standalone runtime process.

    Returns both the service and its synchronous database engine so
    the caller can dispose the engine during shutdown.
    """

    engine = create_database_engine()
    session_factory = create_session_factory(engine)

    service = create_functionality_control_service(
        session_factory=session_factory,
    )

    return service, engine


__all__ = [
    "create_functionality_control_service",
    "create_standalone_functionality_control_service",
]




