"""
Voice Call Repository Infrastructure Adapter.

Infrastructure implementation for
VoiceCall persistence.

Responsibilities:
- Implement application repository contract.
- Provide persistence boundary.
- Hide storage implementation details.

Does NOT:
- Handle HTTP.
- Manage LiveKit.
- Execute AI runtime.
- Send notifications.
- Own business lifecycle rules.

Beta implementation:
- In-memory storage placeholder.
- Replace with SQLAlchemy implementation
  when existing persistence pattern is confirmed.
"""

from __future__ import annotations


from backend.app.application.uai.voice.voice_call_repository import (
    VoiceCallRepository,
)


from app.domain.uai.voice.voice_call import (
    VoiceCall,
)



class InMemoryVoiceCallRepository(
    VoiceCallRepository,
):
    """
    Temporary infrastructure repository.

    Keeps persistence boundary ready
    without introducing a new database
    implementation prematurely.
    """



    def __init__(self) -> None:
        """
        Initialise storage.
        """

        self._storage: dict[
            str,
            VoiceCall,
        ] = {}



    def save(
        self,
        *,
        voice_call: VoiceCall,
    ) -> VoiceCall:
        """
        Store voice call.
        """


        self._storage[
            voice_call.id
        ] = voice_call


        return voice_call



    def get_by_id(
        self,
        *,
        voice_call_id: str,
    ) -> VoiceCall | None:
        """
        Retrieve voice call.
        """


        return self._storage.get(
            voice_call_id,
        )



__all__ = [
    "InMemoryVoiceCallRepository",
]
