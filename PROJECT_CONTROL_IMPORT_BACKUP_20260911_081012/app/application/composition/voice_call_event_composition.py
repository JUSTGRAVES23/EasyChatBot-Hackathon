"""
Voice Call Event Composition.

Composition root for voice lifecycle events.

Responsibilities:
- Build event dependencies.
- Wire event service.
- Provide configured application service.

Does NOT:
- Handle HTTP.
- Create business events.
- Execute workflows.
- Persist directly.
"""

from __future__ import annotations

from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)

from app.application.composition.voice_call_event_dependencies import (
    voice_call_event_repository,
)


def create_voice_call_event_service(
) -> VoiceCallEventService:
    """
    Create configured voice call event service.
    """

    return VoiceCallEventService(
        repository=(
            voice_call_event_repository
        ),
    )


def build_voice_call_event_service(
) -> VoiceCallEventService:
    """
    Dependency builder.

    Used by application adapters
    and other composition roots.
    """

    return (
        create_voice_call_event_service()
    )


__all__ = [
    "create_voice_call_event_service",
    "build_voice_call_event_service",
]

