from __future__ import annotations

from app.application.announcements.repositories import PublicationRepository
from app.domain.announcements.publication import Publication
from app.infrastructure.announcements.sqlalchemy_publication_repository import (
    SqlAlchemyPublicationRepository,
)


class AsyncPublicationRepositoryAdapter(PublicationRepository):
    """Synchronous application contract adapter for the async PostgreSQL adapter.

    This adapter is intentionally not used from an async event loop. It exists
    for compatibility with the current synchronous AnnouncementPublicationService
    contract. Production composition should prefer an async application boundary
    when the application service is migrated.

    Calling these methods from an active async event loop would require blocking
    the loop, so this adapter fails closed rather than performing unsafe
    synchronous database I/O.
    """

    def __init__(self, repository: SqlAlchemyPublicationRepository) -> None:
        if repository is None:
            raise ValueError("repository cannot be None.")
        self._repository = repository

    def _reject_sync_boundary(self) -> None:
        raise RuntimeError(
            "AsyncPublicationRepositoryAdapter cannot be used through the "
            "synchronous PublicationRepository contract. Use the async "
            "approval composition."
        )

    def save(self, publication: Publication) -> None:
        self._reject_sync_boundary()

    def get(self, publication_id: str) -> Publication | None:
        self._reject_sync_boundary()
        return None

    def list_all(self) -> tuple[Publication, ...]:
        self._reject_sync_boundary()
        return ()

