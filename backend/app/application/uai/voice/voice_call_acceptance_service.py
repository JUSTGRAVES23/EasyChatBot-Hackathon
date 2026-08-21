"""
Voice Call Acceptance Service.

Application workflow responsible for
accepting a learner voice call invitation.

Responsibilities:
- Accept notification action.
- Retrieve invitation.
- Retrieve voice call.
- Handle first connection.
- Handle reconnect flow.
- Create voice session.
- Record acceptance event.

Does NOT:
- Handle HTTP.
- Send notifications.
- Connect LiveKit.
- Manage providers.
"""

from __future__ import annotations



from dataclasses import dataclass



from datetime import (
    datetime,
    timezone,
)



from backend.app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)



from backend.app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
)



from backend.app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)



from backend.app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)



from backend.app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)



from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



from app.domain.uai.voice.voice_call_event import (
    VoiceCallEventType,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallAcceptanceService:
    """
    Workflow service for accepting
    voice call notifications.
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

    voice_call_session_service: (
        VoiceCallSessionService
    )

    voice_call_event_service: (
        VoiceCallEventService
    )



    def accept_voice_call(
        self,
        *,
        notification,
    ) -> dict:
        """
        Accept notification and prepare
        voice session.
        """



        updated_notification = (
            self.voice_call_notification_service
            .action_notification(
                notification=notification,
            )
        )



        invitation = (
            self.voice_call_invitation_service
            .get_invitation(
                invitation_id=(
                    notification.invitation_id
                ),
            )
        )



        if invitation is None:

            raise ValueError(
                "Voice call invitation not found."
            )



        voice_call = (
            self.voice_call_management_service
            .get_call(
                voice_call_id=(
                    invitation.voice_call_id
                ),
            )
        )



        if voice_call is None:

            raise ValueError(
                "Voice call not found."
            )



        if voice_call.state == (
            VoiceCallState.CREATED
        ):

            session = (
                self.voice_call_session_service
                .create_session(
                    voice_call=voice_call,
                )
            )


        elif self.voice_call_management_service.can_reconnect(
            voice_call_id=voice_call.id,
            now=datetime.now(
                timezone.utc
            ),
        ):

            session = (
                self.voice_call_session_service
                .reconnect_session(
                    voice_call=voice_call,
                )
            )


        else:

            raise ValueError(
                "Voice call cannot be started."
            )



        self.voice_call_event_service.record_event(
            voice_call_id=voice_call.id,
            learner_id=voice_call.learner_id,
            character_id=voice_call.character_id,
            event_type=(
                VoiceCallEventType.ACCEPTED
            ),
        )



        return {
            "notification": updated_notification,
            "voice_call": voice_call,
            "session": session,
        }



__all__ = [
    "VoiceCallAcceptanceService",
]
