"""
Voice Connection Token Domain Model.

Represents provider-independent credentials
required to connect to a voice room.

Responsibilities:
- Preserve connection token identity.
- Preserve room and provider information.
- Validate token expiration.
- Support both legacy naive UTC datetimes
  and timezone-aware UTC datetimes.

Does NOT:
- Generate provider tokens.
- Connect to LiveKit.
- Handle HTTP.
- Persist credentials.
"""


from __future__ import annotations


from dataclasses import dataclass


from datetime import (
    datetime,
    timezone,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceConnectionToken:
    """
    Provider-independent voice connection token.
    """

    token: str

    room_name: str

    provider: str

    expires_at: datetime



    def __post_init__(
        self,
    ) -> None:
        """
        Validate token invariants.

        The existing application supports legacy
        naive UTC datetimes.

        New infrastructure integrations such as
        LiveKit may provide timezone-aware UTC
        datetimes.

        The domain therefore accepts both forms
        while performing expiration validation
        using UTC-aware values internally.
        """



        if not self.token.strip():

            raise ValueError(
                "token cannot be empty."
            )



        if not self.room_name.strip():

            raise ValueError(
                "room_name cannot be empty."
            )



        if not self.provider.strip():

            raise ValueError(
                "provider cannot be empty."
            )



        expiration_utc = (
            self._to_utc(
                self.expires_at
            )
        )



        now_utc = (
            datetime.now(
                timezone.utc
            )
        )



        if expiration_utc <= now_utc:

            raise ValueError(
                "expires_at must be in the future."
            )



    @staticmethod
    def _to_utc(
        value: datetime,
    ) -> datetime:
        """
        Convert a datetime to timezone-aware UTC
        for internal validation.

        Naive datetimes are treated as legacy UTC.

        The original value is intentionally preserved
        on the immutable domain object so existing
        callers and contracts remain compatible.
        """



        if value.tzinfo is None:

            return value.replace(
                tzinfo=timezone.utc
            )



        return value.astimezone(
            timezone.utc
        )



__all__ = [
    "VoiceConnectionToken",
]