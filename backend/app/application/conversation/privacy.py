from __future__ import annotations

import hashlib
import os


def pseudonymize_identifier(value: str) -> str:
    salt = os.getenv(
        "EVENT_PRIVACY_SALT",
        "change-me-in-production",
    )

    return hashlib.sha256(
        f"{salt}:{value}".encode("utf-8")
    ).hexdigest()
