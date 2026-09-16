"""
Voice Lifecycle Composition.

Composition root for the complete
voice call lifecycle application service.

Responsibilities:
- Build lifecycle dependencies.
- Wire execution coordinator.
- Wire connection services.
- Wire persistent voice call services.
- Wire lifecycle event services.
- Return ready application facade.

Does NOT:
- Handle HTTP.
- Execute voice calls.
- Manage providers.
- Persist data directly.
"""

from __future__ import annotations

from app.application.uai.voice.voice_call_lifecycle_service import (
    VoiceCallLifecycleService,
)

from app.application.composition.voice_execution_coordinator_composition import (
    create_voice_call_execution_coordinator,
)

from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)

from app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)

from app.application.composition.voice_connection_composition import (
    create_voice_connection_service,
)

from app.application.composition.voice_call_dependencies import (
    voice_call_repository,
)

from app.application.composition.voice_call_event_composition import (
    build_voice_call_event_service,
)


def create_voice_call_lifecycle_service(
) -> VoiceCallLifecycleService:
    """
    Create configured voice lifecycle service.
    """

    execution_coordinator = create_voice_call_execution_coordinator()

    connection_service = (
        create_voice_connection_service()
    )

    voice_call_management_service = (
        VoiceCallManagementService(
            repository=(
                voice_call_repository
            ),
        )
    )

    voice_call_session_service = (
        VoiceCallSessionService()
    )

    voice_call_event_service = (
        build_voice_call_event_service()
    )

    return VoiceCallLifecycleService(
        execution_coordinator=(
            execution_coordinator
        ),
        connection_service=(
            connection_service
        ),
        voice_call_management_service=(
            voice_call_management_service
        ),
        voice_call_session_service=(
            voice_call_session_service
        ),
        voice_call_event_service=(
            voice_call_event_service
        ),
    )


def build_voice_call_lifecycle_service(
) -> VoiceCallLifecycleService:
    """
    Dependency builder for application adapters.

    Keeps API composition isolated from
    internal dependency creation.
    """

    return (
        create_voice_call_lifecycle_service()
    )


__all__ = [
    "create_voice_call_lifecycle_service",
    "build_voice_call_lifecycle_service",
]

