from __future__ import annotations


import hashlib
import hmac
import os



class PrivacyIdentifierService:
    """
    Privacy identity pseudonymisation service.

    Converts sensitive identifiers into
    stable pseudonymous identifiers.

    Example:

        Telegram ID
             |
             v
        HMAC SHA256
             |
             v
        anonymous hash


    Security:

    - raw identifiers never stored
    - deterministic output
    - secret protected
    - suitable for analytics correlation

    Does NOT:
    - authenticate users
    - authorize users
    - store mappings
    """


    def __init__(
        self,
        *,
        secret: str | None = None,
    ) -> None:


        self._secret = (
            secret
            or os.getenv(
                "PRIVACY_HASH_SECRET"
            )
        )


        if not self._secret:
            raise RuntimeError(
                "PRIVACY_HASH_SECRET is required."
            )



    def pseudonymize_identifier(
        self,
        identifier: str,
    ) -> str:
        """
        Generate stable pseudonymous identifier.
        """


        if not identifier:
            raise ValueError(
                "identifier cannot be empty."
            )


        digest = hmac.new(
            self._secret.encode("utf-8"),
            identifier.encode("utf-8"),
            hashlib.sha256,
        )


        return digest.hexdigest()