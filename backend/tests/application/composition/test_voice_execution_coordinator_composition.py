"""
Tests for Voice Execution Coordinator Composition.

Validates that the composition root
creates a correctly wired voice execution
coordinator.
"""

from app.application.composition.voice_execution_coordinator_composition import (
    create_voice_call_execution_coordinator,
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



def test_create_voice_call_execution_coordinator():
    """
    Verify composition creates the coordinator.
    """


    coordinator = (
        create_voice_call_execution_coordinator()
    )


    assert isinstance(
        coordinator,
        VoiceCallExecutionCoordinator,
    )


    assert isinstance(
        coordinator.room_service,
        VoiceRoomService,
    )


    assert isinstance(
        coordinator.execution_runtime,
        VoiceCallExecutionRuntime,
    )