from __future__ import annotations

import os
from dataclasses import dataclass


_TRUE_VALUES = {
    "1",
    "true",
    "yes",
    "on",
}

_FALSE_VALUES = {
    "0",
    "false",
    "no",
    "off",
}


@dataclass(frozen=True)
class AcademyActivationConfig:
    """
    Controlled Academy production activation configuration.

    Production activation is disabled unless both explicit
    activation switches are enabled.
    """

    scheduler_enabled: bool
    first_run_enabled: bool

    @classmethod
    def from_environment(cls) -> "AcademyActivationConfig":
        return cls(
            scheduler_enabled=_read_bool(
                "EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED",
                default=False,
            ),
            first_run_enabled=_read_bool(
                "EASYCHATBOT_ACADEMY_FIRST_RUN_ENABLED",
                default=False,
            ),
        )

    @property
    def activation_allowed(self) -> bool:
        return (
            self.scheduler_enabled
            and self.first_run_enabled
        )


def _read_bool(
    name: str,
    *,
    default: bool,
) -> bool:
    raw = os.getenv(name)

    if raw is None:
        return default

    value = raw.strip().lower()

    if value in _TRUE_VALUES:
        return True

    if value in _FALSE_VALUES:
        return False

    raise RuntimeError(
        f"{name} must be a boolean value: "
        "true/false, yes/no, on/off, or 1/0."
    )


__all__ = [
    "AcademyActivationConfig",
]
