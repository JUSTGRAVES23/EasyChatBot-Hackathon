from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeActorContext:
    """Provider-independent authenticated actor context for Runtime governance."""

    actor_id: str
    roles: frozenset[str]

    def __post_init__(self) -> None:
        if not isinstance(self.actor_id, str) or not self.actor_id.strip():
            raise ValueError("Runtime actor_id cannot be empty.")

        if not isinstance(self.roles, frozenset):
            raise ValueError("Runtime actor roles must be a frozenset.")

        if any(
            not isinstance(role, str) or not role.strip()
            for role in self.roles
        ):
            raise ValueError(
                "Runtime actor roles must contain non-empty strings."
            )
