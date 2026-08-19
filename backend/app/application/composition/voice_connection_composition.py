"""
Voice Connection Composition.

Composition root for voice connection
application services.

Responsibilities:
- Build token dependencies.
- Wire infrastructure adapters.
- Return ready application services.

Does NOT:
- Handle HTTP.
- Generate tokens directly.
- Execute voice calls.
- Persist credentials.
"""

from __future__ import annotations


from app.application.uai.voice.voice_connection_service import (
    VoiceConnectionService,
)


from app.infrastructure.voice.livekit_token_service import (
    LiveKitTokenService,
)



def create_voice_connection_service(
) -> VoiceConnectionService:
    """
    Create configured voice connection service.
    """


    token_service = LiveKitTokenService()


    return VoiceConnectionService(
        token_service=token_service,
    )



def build_voice_connection_service(
) -> VoiceConnectionService:
    """
    Dependency builder for application adapters.

    Keeps dependency creation outside
    HTTP and application workflows.
    """


    return (
        create_voice_connection_service()
    )



__all__ = [
    "create_voice_connection_service",
    "build_voice_connection_service",
]