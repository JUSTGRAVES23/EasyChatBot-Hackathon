"""
Voice Call Repository Contract.

Application boundary for storing and
retrieving persistent voice calls.

Responsibilities:
- Define voice call persistence contract.
- Allow lifecycle services to retrieve
  existing voice calls.

Does NOT:
- Connect directly to databases.
- Execute SQL.
- Manage migrations.
- Handle HTTP.
- Manage LiveKit.
"""

from __future__ import annotations


from abc import (
    ABC,
    abstractmethod,
)


from app.domain.uai.voice.voice_call import (
    VoiceCall,
)



class VoiceCallRepository(
    ABC,
):
    """
    Abstract repository contract
    for VoiceCall aggregates.
    """



    @abstractmethod
    def save(
        self,
        *,
        voice_call: VoiceCall,
    ) -> VoiceCall:
        """
        Persist a voice call.

        Returns:
            Saved voice call aggregate.
        """

        raise NotImplementedError



    @abstractmethod
    def get_by_id(
        self,
        *,
        voice_call_id: str,
    ) -> VoiceCall | None:
        """
        Retrieve voice call by identity.
        """

        raise NotImplementedError



__all__ = [
    "VoiceCallRepository",
]
