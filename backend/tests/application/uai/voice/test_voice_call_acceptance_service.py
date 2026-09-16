"""
Tests for Voice Call Acceptance Service.

Validates:

Notification
      |
      ↓
Acceptance
      |
      ↓
VoiceCall
      |
      ↓
Session
      |
      ↓
Execution Context
      |
      ↓
VoiceCallExecutionCoordinator
      |
      ↓
VoiceCallEvent

Identity must remain unchanged.
"""

from app.application.uai.voice.voice_call_acceptance_service import (
    VoiceCallAcceptanceService,
)

from app.application.uai.voice.voice_call_context_factory import (
    VoiceCallContextFactory,
)

from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)

from app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
)

from app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)

from app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)

from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)

from app.infrastructure.persistence.voice_call_repository import (
    InMemoryVoiceCallRepository,
)

from app.infrastructure.persistence.in_memory_voice_call_notification_repository import (
    InMemoryVoiceCallNotificationRepository,
)

from app.infrastructure.persistence.in_memory_voice_call_invitation_repository import (
    InMemoryVoiceCallInvitationRepository,
)

from app.infrastructure.persistence.in_memory_voice_call_event_repository import (
    InMemoryVoiceCallEventRepository,
)

from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotificationChannel,
)

from app.domain.uai.voice.voice_call_event import (
    VoiceCallEventType,
)


class FakeVoiceCallExecutionCoordinator:
    """Test double for the canonical execution coordinator."""

    def __init__(self):
        self.contexts = []

    def start(self, *, context):
        self.contexts.append(context)

        return {
            "room": context.room,
            "session": context.session,
        }


def create_service():
    voice_call_management = (
        VoiceCallManagementService(
            repository=(
                InMemoryVoiceCallRepository()
            ),
        )
    )

    invitation_service = (
        VoiceCallInvitationService(
            repository=(
                InMemoryVoiceCallInvitationRepository()
            ),
        )
    )

    notification_service = (
        VoiceCallNotificationService(
            repository=(
                InMemoryVoiceCallNotificationRepository()
            ),
        )
    )

    event_service = (
        VoiceCallEventService(
            repository=(
                InMemoryVoiceCallEventRepository()
            ),
        )
    )

    session_service = (
        VoiceCallSessionService()
    )

    context_factory = (
        VoiceCallContextFactory()
    )

    execution_coordinator = (
        FakeVoiceCallExecutionCoordinator()
    )

    service = VoiceCallAcceptanceService(
        voice_call_management_service=(
            voice_call_management
        ),
        voice_call_invitation_service=(
            invitation_service
        ),
        voice_call_notification_service=(
            notification_service
        ),
        voice_call_session_service=(
            session_service
        ),
        voice_call_event_service=(
            event_service
        ),
        voice_call_context_factory=(
            context_factory
        ),
        voice_call_execution_coordinator=(
            execution_coordinator
        ),
    )

    return (
        service,
        voice_call_management,
        invitation_service,
        notification_service,
        event_service,
        execution_coordinator,
    )


def test_accept_voice_call_preserves_identity():
    (
        service,
        voice_call_management,
        invitation_service,
        notification_service,
        event_service,
        execution_coordinator,
    ) = create_service()

    voice_call = (
        voice_call_management
        .create_call(
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
        )
    )

    invitation = (
        invitation_service
        .create_invitation(
            voice_call_id=voice_call.id,
            learner_id="learner-001",
            character_id="yeti",
            channel="notification",
        )
    )

    notification = (
        notification_service
        .create_notification(
            invitation_id=invitation.id,
            voice_call_id=voice_call.id,
            learner_id="learner-001",
            character_id="yeti",
            channel=(
                VoiceCallNotificationChannel.INBOX
            ),
        )
    )

    result = (
        service.accept_voice_call(
            notification=notification,
        )
    )

    assert result["voice_call"].id == (
        voice_call.id
    )

    assert result["session"].character_id == (
        "yeti"
    )

    assert result["session"].learner_id == (
        "learner-001"
    )

    assert len(
        execution_coordinator.contexts
    ) == 1

    context = (
        execution_coordinator.contexts[0]
    )

    assert context.voice_call is voice_call

    assert context.session is (
        result["session"]
    )

    assert context.session.learner_id == (
        "learner-001"
    )

    assert context.session.character_id == (
        "yeti"
    )

    assert context.room.room_id == (
        result["session"].session_id
    )

    events = (
        event_service.get_events(
            voice_call_id=voice_call.id,
        )
    )

    assert len(events) == 1

    assert events[0].event_type == (
        VoiceCallEventType.ACCEPTED
    )

