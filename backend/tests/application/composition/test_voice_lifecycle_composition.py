"""
Tests for Voice Lifecycle Composition.

Validates that the composition root
creates a correctly wired voice lifecycle
application service.
"""

from app.application.composition.voice_lifecycle_composition import (
    create_voice_call_lifecycle_service,
)


from app.application.uai.voice.voice_call_lifecycle_service import (
    VoiceCallLifecycleService,
)


from app.application.uai.voice.voice_call_execution_coordinator import (
    VoiceCallExecutionCoordinator,
)


from app.application.uai.voice.voice_room_service import (
    VoiceRoomService,
)


from app.ai_runtime.voice.voice_call_execution_runtime import (
    VoiceCallExecutionRuntime,
)



def test_create_voice_call_lifecycle_service():
    """
    Verify lifecycle service creation.
    """


    service = (
        create_voice_call_lifecycle_service()
    )


    assert isinstance(
        service,
        VoiceCallLifecycleService,
    )


    assert isinstance(
        service.execution_coordinator,
        VoiceCallExecutionCoordinator,
    )


    assert isinstance(
        service.execution_coordinator.room_service,
        VoiceRoomService,
    )


    assert isinstance(
        service.execution_coordinator.execution_runtime,
        VoiceCallExecutionRuntime,
    )