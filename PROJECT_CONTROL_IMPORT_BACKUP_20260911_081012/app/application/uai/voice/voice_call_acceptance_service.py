from __future__ import annotations

from dataclasses import dataclass

from app.application.uai.voice.voice_call_context_factory import (
    VoiceCallContextFactory,
)
from app.application.uai.voice.voice_call_execution_coordinator import (
    VoiceCallExecutionCoordinator,
)
from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)
from app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
)
from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)
from app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)
from app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)
from app.domain.uai.voice.voice_call import VoiceCall
from app.domain.uai.voice.voice_call_event import VoiceCallEventType
from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotification,
)


@dataclass
class VoiceCallAcceptanceService:
    """
    Application service responsible for accepting an incoming voice-call
    notification and converging the acceptance workflow into the canonical
    voice execution path.

    Responsibilities:
    - Resolve the actionable notification.
    - Resolve and validate the associated invitation.
    - Resolve the associated VoiceCall.
    - Create or reconnect the authoritative VoiceCallSession.
    - Build the execution context from that existing session.
    - Delegate execution to VoiceCallExecutionCoordinator.
    - Record the ACCEPTED lifecycle event.

    This service does not:
    - Access LiveKit directly.
    - Construct infrastructure providers.
    - Persist directly.
    - Implement voice execution itself.
    """

    voice_call_management_service: VoiceCallManagementService
    voice_call_invitation_service: VoiceCallInvitationService
    voice_call_notification_service: VoiceCallNotificationService
    voice_call_session_service: VoiceCallSessionService
    voice_call_event_service: VoiceCallEventService
    voice_call_context_factory: VoiceCallContextFactory
    voice_call_execution_coordinator: VoiceCallExecutionCoordinator

    def accept_voice_call(
        self,
        notification: VoiceCallNotification,
    ) -> dict[str, object]:
        """
        Accept a voice-call notification and start the canonical execution
        workflow using the authoritative VoiceCallSession.
        """

        actionable_notification = (
            self.voice_call_notification_service.action_notification(
                notification
            )
        )

        invitation = self.voice_call_invitation_service.get_invitation(
            actionable_notification.invitation_id
        )

        voice_call = self.voice_call_management_service.get_voice_call(
            invitation.voice_call_id
        )

        if voice_call is None:
            raise ValueError(
                f"Voice call not found: {invitation.voice_call_id}"
            )

        if voice_call.state == "CREATED":
            session = self.voice_call_session_service.create_session(
                voice_call
            )
        elif self.voice_call_session_service.can_reconnect(voice_call):
            session = self.voice_call_session_service.reconnect_session(
                voice_call
            )
        else:
            raise ValueError(
                f"Voice call cannot be accepted in state: {voice_call.state}"
            )

        context = self.voice_call_context_factory.create_from_session(
            session=session,
            voice_call=voice_call,
        )

        self.voice_call_execution_coordinator.start(
            context=context,
        )

        self.voice_call_event_service.record_event(
            voice_call_id=voice_call.id,
            event_type=VoiceCallEventType.ACCEPTED,
        )

        return {
            "notification": actionable_notification,
            "voice_call": voice_call,
            "session": session,
        }


__all__ = ["VoiceCallAcceptanceService"]

