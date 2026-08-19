"""
Tests for Voice Execution Composition.

Validates that the composition root
creates correctly wired voice execution
application services.
"""

from app.application.composition.voice_execution_composition import (
    create_voice_call_execution_service,
)


from app.application.uai.voice.voice_call_execution_service import (
    VoiceCallExecutionService,
)


from app.ai_runtime.voice.voice_call_execution_runtime import (
    VoiceCallExecutionRuntime,
)



def test_create_voice_call_execution_service():
    """
    Verify composition creates
    the application service.
    """


    service = (
        create_voice_call_execution_service()
    )


    assert isinstance(
        service,
        VoiceCallExecutionService,
    )


    assert isinstance(
        service.execution_runtime,
        VoiceCallExecutionRuntime,
    )