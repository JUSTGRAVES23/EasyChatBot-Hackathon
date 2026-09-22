"""Application port for the canonical Platform Intelligence review projection."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any


class PlatformIntelligenceReviewSource(ABC):
    """Read-only application port for PI human-review projections.

    The backend deliberately depends on this port rather than importing or
    constructing Platform Intelligence runtime services. A production adapter
    can bind this port to the canonical ``ai_agents`` runtime integration.
    """

    @abstractmethod
    def list_reviews(self) -> Sequence[Any]:
        """Return current governed review projections."""
        raise NotImplementedError

    @abstractmethod
    def get_review(self, review_item_id: str) -> Any | None:
        """Return one governed review projection, if available."""
        raise NotImplementedError

    @abstractmethod
    def list_escalations(self) -> Sequence[Any]:
        """Return governed review projections with escalation recommendations."""
        raise NotImplementedError


class UnconfiguredPlatformIntelligenceReviewSource(PlatformIntelligenceReviewSource):
    """Safe inert source object when the canonical PI integration is absent.

    The application API intentionally uses ``source=None`` to distinguish
    an unconfigured integration from a valid empty result set. This class is
    retained as an explicit port implementation for composition/tests and is
    not used as the default API source.
    """

    def list_reviews(self) -> Sequence[Any]:
        return ()

    def get_review(self, review_item_id: str) -> Any | None:
        return None

    def list_escalations(self) -> Sequence[Any]:
        return ()
