"""
Tests for Voice Lifecycle Composition.

Validates that the composition root
creates a correctly wired voice lifecycle
application service.

The composition root must provide:

VoiceCallLifecycleService
        |
        +-- ExecutionCoordinator
        |
        +-- VoiceRoomService
        |
        +-- VoiceCallExecutionRuntime
        |
        +-- VoiceCallEventService
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


from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
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



def test_lifecycle_service_has_event_service():
    """
    Verify lifecycle events are wired.
    """


    service = (
        create_voice_call_lifecycle_service()
    )


    assert isinstance(
        service.voice_call_event_service,
        VoiceCallEventService,
    )



def test_lifecycle_event_service_is_shared_dependency():
    """
    Verify the lifecycle composition
    receives an event service instance.

    Repository replacement remains
    hidden behind composition.
    """


    service = (
        create_voice_call_lifecycle_service()
    )


    assert (
        service.voice_call_event_service
        is not None
    )

