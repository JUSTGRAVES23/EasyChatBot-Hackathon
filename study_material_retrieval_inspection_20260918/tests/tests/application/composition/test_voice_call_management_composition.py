"""
Tests for Voice Call Management Composition.

Validates that the composition root
creates a correctly wired VoiceCallManagementService.

Responsibilities verified:
- Service creation.
- Repository dependency injection.
- Application layer isolation.
"""

from app.application.composition.voice_call_management_composition import (
    create_voice_call_management_service,
    build_voice_call_management_service,
)


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.infrastructure.persistence.voice_call_repository import (
    InMemoryVoiceCallRepository,
)



def test_create_voice_call_management_service():
    """
    Verify composition creates a configured
    voice call management service.
    """


    service = (
        create_voice_call_management_service()
    )


    assert isinstance(
        service,
        VoiceCallManagementService,
    )


    assert service.repository is not None


    assert isinstance(
        service.repository,
        InMemoryVoiceCallRepository,
    )



def test_build_voice_call_management_service():
    """
    Verify dependency builder returns
    a configured application service.
    """


    service = (
        build_voice_call_management_service()
    )


    assert isinstance(
        service,
        VoiceCallManagementService,
    )


    assert service.repository is not None



def test_repository_can_store_voice_call():

    service = (
        create_voice_call_management_service()
    )


    voice_call = (
        service.create_call(
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
        )
    )


    result = (
        service.get_call(
            voice_call_id=voice_call.id,
        )
    )


    assert result is not None


    assert result.id == (
        voice_call.id
    )

