"""
Voice Execution Composition.

Application composition root
for voice call execution services.

Responsibilities:
- Build execution dependencies.
- Wire application services.

Does NOT:
- Handle HTTP.
- Execute calls.
- Persist data.
- Manage providers.
"""

from __future__ import annotations


from backend.app.application.uai.voice.voice_call_execution_service import (
    VoiceCallExecutionService,
)


from app.ai_runtime.voice.voice_call_execution_runtime import (
    VoiceCallExecutionRuntime,
)



def create_voice_call_execution_service(
) -> VoiceCallExecutionService:
    """
    Create configured voice execution service.
    """


    runtime = (
        VoiceCallExecutionRuntime()
    )


    return VoiceCallExecutionService(
        execution_runtime=runtime,
    )



def build_voice_call_execution_service(
) -> VoiceCallExecutionService:
    """
    Dependency builder.

    Used by application composition
    and adapters.
    """


    return (
        create_voice_call_execution_service()
    )



__all__ = [
    "create_voice_call_execution_service",
    "build_voice_call_execution_service",
]
