"""
Voice Call Trigger Service.

Application workflow service responsible
for starting the voice call invitation flow.

Responsibilities:
- Create voice call identity.
- Activate voice call lifecycle.
- Record lifecycle events.
- Create voice call invitation.
- Create notification trigger.
- Coordinate application services.

Does NOT:
- Send emails.
- Send notifications.
- Execute AI runtime.
- Connect LiveKit.
- Manage persistence directly.
"""

from __future__ import annotations


from dataclasses import dataclass



from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
)


from app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)


from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)



from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotificationChannel,
)


from app.domain.uai.voice.voice_call_event import (
    VoiceCallEventType,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallTriggerService:
    """
    Application workflow coordinator
    for voice call triggering.
    """


    voice_call_management_service: (
        VoiceCallManagementService
    )


    voice_call_invitation_service: (
        VoiceCallInvitationService
    )


    voice_call_notification_service: (
        VoiceCallNotificationService
    )


    voice_call_event_service: (
        VoiceCallEventService
    )



    def trigger_voice_call(
        self,
        *,
        learner_id: str,
        character_id: str,
        world_id: str,
        language_code: str,
        notification_channel: VoiceCallNotificationChannel,
    ) -> dict:
        """
        Create complete voice call trigger flow.
        """



        voice_call = (
            self.voice_call_management_service
            .create_call(
                learner_id=learner_id,
                character_id=character_id,
                world_id=world_id,
                language_code=language_code,
            )
        )



        #
        # Voice call becomes active after
        # trigger workflow starts.
        #
        # This enables:
        # - reconnect validation
        # - lifecycle tracking
        # - session recovery
        #

        active_voice_call = (
            voice_call
            .mark_active()
        )



        active_voice_call = (
            self.voice_call_management_service
            .repository
            .save(
                voice_call=active_voice_call,
            )
        )



        #
        # Record business lifecycle event.
        #
        # This is independent from:
        # - LiveKit events
        # - AI runtime telemetry
        #

        self.voice_call_event_service.record_event(
            voice_call_id=(
                active_voice_call.id
            ),
            learner_id=learner_id,
            character_id=character_id,
            event_type=(
                VoiceCallEventType.CREATED
            ),
        )



        invitation = (
            self.voice_call_invitation_service
            .create_invitation(
                voice_call_id=active_voice_call.id,
                learner_id=learner_id,
                character_id=character_id,
                channel=(
                    notification_channel.value
                ),
            )
        )



        notification = (
            self.voice_call_notification_service
            .create_notification(
                invitation_id=invitation.id,
                voice_call_id=active_voice_call.id,
                learner_id=learner_id,
                character_id=character_id,
                channel=(
                    notification_channel
                ),
            )
        )



        return {
            "voice_call": active_voice_call,
            "invitation": invitation,
            "notification": notification,
        }



__all__ = [
    "VoiceCallTriggerService",
]


