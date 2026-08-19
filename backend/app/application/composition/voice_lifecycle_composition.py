"""
Voice Lifecycle Composition.

Composition root for the complete
voice call lifecycle application service.

Responsibilities:
- Build lifecycle dependencies.
- Wire execution coordinator.
- Wire connection services.
- Wire persistent voice call services.
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


from app.application.uai.voice.voice_call_execution_coordinator import (
    VoiceCallExecutionCoordinator,
)


from app.application.uai.voice.voice_room_service import (
    VoiceRoomService,
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


from app.infrastructure.voice.voice_room_adapter import (
    VoiceRoomAdapter,
)


from app.infrastructure.persistence.voice_call_repository import (
    InMemoryVoiceCallRepository,
)


from app.ai_runtime.voice.voice_call_execution_runtime import (
    VoiceCallExecutionRuntime,
)



def create_voice_call_lifecycle_service(
) -> VoiceCallLifecycleService:
    """
    Create configured voice lifecycle service.
    """


    room_service = VoiceRoomService(
        room_adapter=(
            VoiceRoomAdapter()
        ),
    )


    execution_runtime = (
        VoiceCallExecutionRuntime()
    )


    execution_coordinator = (
        VoiceCallExecutionCoordinator(
            room_service=room_service,
            execution_runtime=execution_runtime,
        )
    )


    connection_service = (
        create_voice_connection_service()
    )


    voice_call_repository = (
        InMemoryVoiceCallRepository()
    )


    voice_call_management_service = (
        VoiceCallManagementService(
            repository=voice_call_repository,
        )
    )


    voice_call_session_service = (
        VoiceCallSessionService()
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