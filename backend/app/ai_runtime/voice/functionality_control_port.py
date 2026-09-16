"""Runtime port for operational functionality control."""

from __future__ import annotations

from typing import Protocol


class FunctionalityControlPort(Protocol):
    """Minimal control contract required by AI Runtime."""

    def get_availability(
        self,
        *,
        environment: str,
        functionality_id: str,
    ) -> str:
        """Return the current operational availability."""
        ...


__all__ = ["FunctionalityControlPort"]
