"""
Voice Event Composition.

Composition root for voice lifecycle
event services.

Responsibilities:
- Build event dependencies.
- Wire repository implementation.
- Return configured event service.

Does NOT:
- Handle HTTP.
- Execute workflows.
- Manage LiveKit.
- Execute AI runtime.
- Contain business logic.
"""

from __future__ import annotations



from backend.app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)



from app.infrastructure.persistence.in_memory_voice_call_event_repository import (
    InMemoryVoiceCallEventRepository,
)



#
# Beta repository.
#
# Future replacement:
#
# PostgreSQL/Event Store
#
# without changing application services.
#

_voice_call_event_repository = (
    InMemoryVoiceCallEventRepository()
)



def create_voice_call_event_service(
) -> VoiceCallEventService:
    """
    Create configured voice event service.
    """


    return VoiceCallEventService(
        repository=(
            _voice_call_event_repository
        ),
    )



def build_voice_call_event_service(
) -> VoiceCallEventService:
    """
    Dependency builder.

    Used by application adapters
    and workflow composition roots.
    """


    return (
        create_voice_call_event_service()
    )



__all__ = [
    "create_voice_call_event_service",
    "build_voice_call_event_service",
]
