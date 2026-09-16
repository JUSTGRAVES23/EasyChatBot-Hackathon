"""
Voice Call Acceptance Composition.

Composition root for the voice call
acceptance workflow.

Responsibilities:
- Build acceptance dependencies.
- Wire voice services.
- Wire notification services.
- Wire voice event services.
- Wire canonical voice execution.
- Reuse shared application repositories.
- Return configured workflow service.

Does NOT:
- Handle HTTP.
- Send notifications.
- Execute voice runtime directly.
- Manage providers directly.
"""

from __future__ import annotations

from app.application.composition.voice_execution_coordinator_composition import (
    create_voice_call_execution_coordinator,
)

from app.application.composition.voice_call_dependencies import (
    voice_call_repository,
    voice_call_invitation_repository,
    voice_call_notification_repository,
)

from app.application.composition.voice_event_composition import (
    build_voice_call_event_service,
)

from app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)

from app.application.uai.voice.voice_call_acceptance_service import (
    VoiceCallAcceptanceService,
)

from app.application.uai.voice.voice_call_context_factory import (
    VoiceCallContextFactory,
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

from app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)


def create_voice_call_acceptance_service(
) -> VoiceCallAcceptanceService:
    """
    Create configured acceptance workflow.

    Shared repositories ensure trigger,
    acceptance and reconnect flows
    operate on the same application state.
    """

    voice_call_management_service = (
        VoiceCallManagementService(
            repository=voice_call_repository,
        )
    )

    voice_call_invitation_service = (
        VoiceCallInvitationService(
            repository=voice_call_invitation_repository,
        )
    )

    voice_call_notification_service = (
        VoiceCallNotificationService(
            repository=voice_call_notification_repository,
        )
    )

    voice_call_event_service = (
        build_voice_call_event_service()
    )

    voice_call_context_factory = (
        VoiceCallContextFactory()
    )

    voice_call_execution_coordinator = (
        create_voice_call_execution_coordinator()
    )

    return VoiceCallAcceptanceService(
        voice_call_management_service=(
            voice_call_management_service
        ),
        voice_call_invitation_service=(
            voice_call_invitation_service
        ),
        voice_call_notification_service=(
            voice_call_notification_service
        ),
        voice_call_session_service=(
            VoiceCallSessionService()
        ),
        voice_call_event_service=(
            voice_call_event_service
        ),
        voice_call_context_factory=(
            voice_call_context_factory
        ),
        voice_call_execution_coordinator=(
            voice_call_execution_coordinator
        ),
    )


def build_voice_call_acceptance_service(
) -> VoiceCallAcceptanceService:
    """
    Dependency builder.

    Used by API adapters.
    """

    return (
        create_voice_call_acceptance_service()
    )


__all__ = [
    "create_voice_call_acceptance_service",
    "build_voice_call_acceptance_service",
]

