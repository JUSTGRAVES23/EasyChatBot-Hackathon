"""
Voice Call End Service.

Application workflow responsible
for completing a voice call lifecycle.

Responsibilities:
- Complete voice call lifecycle.
- Preserve voice identity.
- Record completion event.

Does NOT:
- Handle HTTP.
- Disconnect LiveKit directly.
- Manage providers.
- Execute AI runtime.
- Delete persistence data.
"""

from __future__ import annotations


from dataclasses import dataclass



from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)


from app.domain.uai.voice.voice_call import (
    VoiceCall,
)


from app.domain.uai.voice.voice_call_event import (
    VoiceCallEventType,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallEndService:
    """
    Application workflow service
    for completing voice calls.
    """


    voice_call_event_service: (
        VoiceCallEventService
    )



    def end_voice_call(
        self,
        *,
        voice_call: VoiceCall,
    ) -> dict:
        """
        Complete voice call lifecycle.

        Returns:
        - completed voice call identity
        - generated lifecycle event
        """


        completed_voice_call = (
            voice_call.mark_completed()
        )


        event = (
            self.voice_call_event_service
            .record_event(
                voice_call_id=(
                    completed_voice_call.id
                ),

                learner_id=(
                    completed_voice_call.learner_id
                ),

                character_id=(
                    completed_voice_call.character_id
                ),

                event_type=(
                    VoiceCallEventType.COMPLETED
                ),
            )
        )


        return {
            "voice_call": completed_voice_call,
            "event": event,
        }



__all__ = [
    "VoiceCallEndService",
]


