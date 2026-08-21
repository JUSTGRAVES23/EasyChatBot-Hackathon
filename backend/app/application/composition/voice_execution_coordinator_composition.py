"""
Voice Execution Coordinator Composition.

Composition root for complete
voice call execution workflow.

Responsibilities:
- Build room services.
- Build runtime services.
- Wire execution coordinator.

Does NOT:
- Handle HTTP.
- Execute calls.
- Manage providers.
- Store data.
"""

from __future__ import annotations


from backend.app.application.uai.voice.voice_call_execution_coordinator import (
    VoiceCallExecutionCoordinator,
)


from backend.app.application.uai.voice.voice_room_service import (
    VoiceRoomService,
)


from app.infrastructure.voice.voice_room_adapter import (
    VoiceRoomAdapter,
)


from app.ai_runtime.voice.voice_call_execution_runtime import (
    VoiceCallExecutionRuntime,
)



def create_voice_call_execution_coordinator(
) -> VoiceCallExecutionCoordinator:
    """
    Create configured voice execution coordinator.
    """


    room_service = VoiceRoomService(
        room_adapter=(
            VoiceRoomAdapter()
        ),
    )


    execution_runtime = (
        VoiceCallExecutionRuntime()
    )


    return VoiceCallExecutionCoordinator(
        room_service=room_service,
        execution_runtime=execution_runtime,
    )



__all__ = [
    "create_voice_call_execution_coordinator",
]
