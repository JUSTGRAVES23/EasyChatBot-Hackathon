"""Access-tier policy for Learning Worlds."""

from __future__ import annotations

from enum import StrEnum


class WorldAccessTier(StrEnum):
    """Authoritative access tier assigned to a Learning World."""

    NORMAL = "normal"
    PREMIUM = "premium"
    SPECIAL = "special"

    @classmethod
    def from_value(cls, value: str) -> "WorldAccessTier":
        """Return the tier represented by a persisted value.

        Unknown values fail closed rather than silently becoming another tier.
        """
        if not isinstance(value, str):
            raise ValueError("World access tier must be a string.")

        normalized = value.strip().lower()

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported World access tier: {value!r}."
            ) from exc


__all__ = ["WorldAccessTier"]