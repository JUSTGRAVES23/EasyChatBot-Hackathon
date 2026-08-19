"""
Tests for Voice Lifecycle Dependency Builder.

Validates the application dependency
entry point used by adapters.
"""

from app.application.composition.voice_lifecycle_composition import (
    build_voice_call_lifecycle_service,
)


from app.application.uai.voice.voice_call_lifecycle_service import (
    VoiceCallLifecycleService,
)


from app.application.uai.voice.voice_call_execution_coordinator import (
    VoiceCallExecutionCoordinator,
)



def test_build_voice_call_lifecycle_service():

    service = (
        build_voice_call_lifecycle_service()
    )


    assert isinstance(
        service,
        VoiceCallLifecycleService,
    )


    assert isinstance(
        service.execution_coordinator,
        VoiceCallExecutionCoordinator,
    )


    assert (
        service.execution_coordinator
        .room_service
        is not None
    )


    assert (
        service.execution_coordinator
        .execution_runtime
        is not None
    )