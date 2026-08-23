from __future__ import annotations

import hashlib
import hmac
import os

class PrivacyIdentifierService:
    def __init__(self, secret=None):
        self._secret = secret or os.getenv('PRIVACY_HASH_SECRET')
        if not self._secret:
            raise RuntimeError('PRIVACY_HASH_SECRET is required.')

    def pseudonymize_identifier(self, value: str) -> str:
        return hmac.new(self._secret.encode(), value.encode(), hashlib.sha256).hexdigest()
