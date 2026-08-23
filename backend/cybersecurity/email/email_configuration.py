"""
Cybersecurity email configuration.

Configuration is environment-driven so email recipients,
sender identity, and provider credentials are not hard-coded
in application logic.

Environment variables take precedence over local .env values.
The .env file is used for local development.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values


# ============================================================
# Project environment
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

ENV_FILE = PROJECT_ROOT / ".env"


def _load_local_env() -> dict[str, Any]:
    """
    Load values from the project .env file.

    Application services do not read .env directly.
    """

    if not ENV_FILE.exists():
        return {}

    return dict(
        dotenv_values(ENV_FILE)
    )


_LOCAL_ENV = _load_local_env()


def _get_config(
    name: str,
    default: str = "",
) -> str:
    """
    Resolve configuration.

    Priority:

    1. Real process environment variable.
    2. Project .env value.
    3. Supplied default.
    """

    environment_value = os.getenv(name)

    if environment_value is not None:
        return environment_value

    dotenv_value = _LOCAL_ENV.get(name)

    if dotenv_value is not None:
        return str(dotenv_value)

    return default


# ============================================================
# Email configuration
# ============================================================

EMAIL_RECIPIENT = _get_config(
    "CYBERSECURITY_RECIPIENT_EMAIL",
    "davdbarbero1999@gmail.com",
)


EMAIL_FROM = _get_config(
    "CYBERSECURITY_EMAIL_FROM",
    "EasyChatBot Cybersecurity <onboarding@resend.dev>",
)


RESEND_API_KEY = _get_config(
    "RESEND_API_KEY",
)


# ============================================================
# Circuit breaker configuration
# ============================================================

EMAIL_FAILURE_THRESHOLD = int(
    _get_config(
        "CYBERSECURITY_EMAIL_FAILURE_THRESHOLD",
        "3",
    )
)


EMAIL_COOLDOWN_MINUTES = int(
    _get_config(
        "CYBERSECURITY_EMAIL_COOLDOWN_MINUTES",
        "30",
    )
)