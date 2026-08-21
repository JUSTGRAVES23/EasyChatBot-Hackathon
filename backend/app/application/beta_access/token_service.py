from __future__ import annotations

import hashlib
import secrets


class BetaConnectionTokenService:
    TOKEN_BYTES = 32

    @classmethod
    def generate(cls) -> tuple[str, str]:
        raw = secrets.token_urlsafe(cls.TOKEN_BYTES)
        return raw, cls.hash_token(raw)

    @staticmethod
    def hash_token(raw_token: str) -> str:
        if not isinstance(raw_token, str) or not raw_token:
            raise ValueError("raw_token must be a non-empty string.")
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
