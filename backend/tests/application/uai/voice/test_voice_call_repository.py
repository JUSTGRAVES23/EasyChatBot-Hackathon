"""
Tests for Voice Call Repository contract.

Validates that the repository boundary
defines the expected persistence contract
for VoiceCall aggregates.
"""

from datetime import datetime, timedelta


from app.application.uai.voice.voice_call_repository import (
    VoiceCallRepository,
)


from app.domain.uai.voice.voice_call import (
    VoiceCall,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



class InMemoryVoiceCallRepository(
    VoiceCallRepository,
):
    """
    Test implementation of repository contract.
    """

    def __init__(self):

        self.storage = {}



    def save(
        self,
        *,
        voice_call: VoiceCall,
    ) -> VoiceCall:

        self.storage[
            voice_call.id
        ] = voice_call

        return voice_call



    def get_by_id(
        self,
        *,
        voice_call_id: str,
    ) -> VoiceCall | None:

        return self.storage.get(
            voice_call_id
        )



def create_voice_call() -> VoiceCall:
    """
    Create valid voice call.
    """

    created_at = datetime.utcnow()


    return VoiceCall(
        id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
        state=VoiceCallState.ACTIVE,
        created_at=created_at,
        expires_at=(
            created_at
            + timedelta(
                minutes=30
            )
        ),
    )



def test_repository_contract_can_save_voice_call():

    repository = (
        InMemoryVoiceCallRepository()
    )


    voice_call = create_voice_call()


    saved = repository.save(
        voice_call=voice_call,
    )


    assert saved.id == (
        "vc-001"
    )


    assert saved.character_id == (
        "yeti"
    )



def test_repository_contract_can_retrieve_voice_call():

    repository = (
        InMemoryVoiceCallRepository()
    )


    voice_call = create_voice_call()


    repository.save(
        voice_call=voice_call,
    )


    result = repository.get_by_id(
        voice_call_id="vc-001",
    )


    assert result is not None


    assert result.id == (
        "vc-001"
    )


    assert result.learner_id == (
        "learner-001"
    )



def test_repository_returns_none_for_unknown_call():

    repository = (
        InMemoryVoiceCallRepository()
    )


    result = repository.get_by_id(
        voice_call_id="unknown",
    )


    assert result is None



def test_repository_implements_contract():

    repository = (
        InMemoryVoiceCallRepository()
    )


    assert isinstance(
        repository,
        VoiceCallRepository,
    )



