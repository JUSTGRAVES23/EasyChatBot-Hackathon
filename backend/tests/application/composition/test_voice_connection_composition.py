"""
Tests for Voice Connection Composition.

Validates that the composition root
creates a correctly wired voice connection
application service.
"""

from app.application.composition.voice_connection_composition import (
    create_voice_connection_service,
    build_voice_connection_service,
)


from app.application.uai.voice.voice_connection_service import (
    VoiceConnectionService,
)


from app.infrastructure.voice.livekit_token_service import (
    LiveKitTokenService,
)



def test_create_voice_connection_service():
    """
    Verify composition creates service.
    """


    service = (
        create_voice_connection_service()
    )


    assert isinstance(
        service,
        VoiceConnectionService,
    )


    assert isinstance(
        service.token_service,
        LiveKitTokenService,
    )



def test_build_voice_connection_service():
    """
    Verify dependency builder returns
    configured application service.
    """


    service = (
        build_voice_connection_service()
    )


    assert isinstance(
        service,
        VoiceConnectionService,
    )


    assert service.token_service is not None

