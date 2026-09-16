"""
Tests for Voice Call Service.
"""

from app.application.uai.voice.voice_call_service import (
    VoiceCallService,
)

from app.application.uai.voice.voice_call_request import (
    VoiceCallRequest,
)

from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)



class FakeVoiceCallOrchestrator:
    """
    Fake orchestrator.

    Keeps test isolated from
    runtime and infrastructure.
    """


    def prepare_call(
        self,
        *,
        request: VoiceCallRequest,
    ) -> VoiceCallSession:
        """
        Return fake prepared session.
        """

        return VoiceCallSession(
            session_id="call-001",
            learner_id=request.learner_id,
            character_id=request.character_id,
            world_id=request.world_id,
            language_code=request.language_code,
        )



def test_prepare_call():

    service = VoiceCallService(
        orchestrator=(
            FakeVoiceCallOrchestrator()
        )
    )


    request = VoiceCallRequest(
        learner_id="learner-001",
        world_id="french_world",
        character_id="yeti",
        language_code="fr",
    )


    response = service.prepare_call(
        request=request
    )


    assert response["room_name"] == (
        "call-001"
    )


    assert response["character_id"] == (
        "yeti"
    )


    assert response["language_code"] == (
        "fr"
    )


    assert response["provider"] == (
        "livekit"
    )



