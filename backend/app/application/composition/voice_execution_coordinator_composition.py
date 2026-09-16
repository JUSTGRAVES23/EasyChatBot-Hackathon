"""
Voice Execution Coordinator Composition.

Shared composition root for the canonical
voice call execution workflow.

Responsibilities:
- Build the provider implementation for the room boundary.
- Build the application room service.
- Build the voice execution runtime.
- Wire the execution coordinator.

Does NOT:
- Handle HTTP.
- Execute calls.
- Persist data.
- Own business workflows.
"""

from __future__ import annotations

from app.application.uai.voice.voice_call_execution_coordinator import (
    VoiceCallExecutionCoordinator,
)
from app.application.uai.voice.voice_room_service import (
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
    Create the canonical voice execution coordinator.

    Provider-specific construction remains in the
    composition root while the application service
    depends only on the VoiceRoomPort contract.
    """

    room_service = VoiceRoomService(
        room_adapter=VoiceRoomAdapter(),
    )

    execution_runtime = VoiceCallExecutionRuntime()

    return VoiceCallExecutionCoordinator(
        room_service=room_service,
        execution_runtime=execution_runtime,
    )


__all__ = [
    "create_voice_call_execution_coordinator",
]

