from __future__ import annotations

from typing import Protocol, Sequence
from uuid import UUID

from app.domain.study_material.study_material import StudyMaterial


class StudyMaterialRepository(Protocol):
    """
    Repository port for Study Material retrieval.

    This is a domain/application boundary.

    Implementations may use PostgreSQL, another persistence
    mechanism, or a test double, but the domain/application
    layers must not depend on those implementation details.

    The initial Study Materials vertical slice is intentionally
    read-only and exposes only published learner-visible
    materials.
    """

    def list_published_by_world(
        self,
        world_id: str,
    ) -> Sequence[StudyMaterial]:
        """
        Return all published Study Materials belonging to a World.

        Parameters
        ----------
        world_id:
            Business-facing Learning World identifier, for example
            ``french_world`` or ``luxembourgish_world``.

        Returns
        -------
        Sequence[StudyMaterial]
            Published materials ordered according to the repository
            contract.

        Notes
        -----
        Learner identity is intentionally not part of this repository
        contract because catalogue visibility is World-based. Any
        learner-specific entitlement or progress logic belongs outside
        this initial catalogue repository.
        """
        ...

    def get_published(
        self,
        material_id: UUID,
        world_id: str,
    ) -> StudyMaterial | None:
        """
        Retrieve one published Study Material belonging to a World.

        Parameters
        ----------
        material_id:
            Stable Study Material UUID.

        world_id:
            Business-facing Learning World identifier.

        Returns
        -------
        StudyMaterial | None
            The published material when it exists and belongs to the
            requested World; otherwise ``None``.

        Security
        --------
        The World identifier is part of the lookup contract so a
        material cannot be returned merely because its UUID exists.
        The application layer remains responsible for validating the
        requested World and enforcing the learner-facing access policy.
        """
        ...