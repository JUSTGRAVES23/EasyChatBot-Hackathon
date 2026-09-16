from __future__ import annotations

from typing import Protocol, Sequence

from .models import KnowledgeResult


class KnowledgeProvider(Protocol):
    """Provider-independent read-only knowledge boundary.

    Implementations may use a filesystem, database, Project Brain repository,
    or another approved internal knowledge source. The Agent must not know
    which storage/search technology is used.
    """

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> Sequence[KnowledgeResult]:
        ...
