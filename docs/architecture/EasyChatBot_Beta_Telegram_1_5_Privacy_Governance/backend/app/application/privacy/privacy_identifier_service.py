from __future__ import annotations

import hashlib
import hmac
import os


class PrivacyIdentifierService:
    def __init__(self, secret: str | None = None) -> None:
        self._secret = secret or os.getenv("PRIVACY_HASH_SECRET")
        if not self._secret:
            raise RuntimeError("PRIVACY_HASH_SECRET is required.")

    def pseudonymize_identifier(self, identifier: str) -> str:
        return hmac.new(
            self._secret.encode("utf-8"),
            identifier.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
