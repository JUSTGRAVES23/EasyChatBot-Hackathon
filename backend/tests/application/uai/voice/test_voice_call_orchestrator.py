"""
Tests for Voice Call Orchestrator.
"""

from app.application.uai.voice.voice_call_orchestrator import (
    VoiceCallOrchestrator,
)

from app.application.uai.voice.voice_call_request import (
    VoiceCallRequest,
)

from app.domain.uai.voice.voice_session import (
    VoiceSession,
)

from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


class FakeVoiceCharacterSessionService:
    """
    Fake character session service.

    Avoids LiveKit and provider dependencies.
    """

    def __init__(self) -> None:
        self.context = None

    def create_session(
        self,
        *,
        context,
    ) -> VoiceSession:
        """
        Create fake voice session and retain context
        for orchestration assertions.
        """

        self.context = context

        return VoiceSession(
            session_id="voice-session-001",
            room_name="room-001",
            character_id=(
                context.character.character_id
            ),
            language_code=(
                context.voice.language_code
            ),
        )


class FakeInteractionContextBuilder:
    """
    Fake interaction context builder.

    Keeps this test focused on orchestration.
    """

    def build(
        self,
        *,
        learner,
        world_id,
        character_id,
        voice,
    ):
        """
        Build minimal interaction context.
        """

        from app.domain.uai.context.character_context import (
            CharacterContext,
        )

        from app.domain.uai.context.interaction_context import (
            InteractionContext,
        )

        from app.domain.uai.context.world_context import (
            WorldContext,
        )

        return InteractionContext(
            learner=learner,
            world=WorldContext(
                world_id=world_id,
                name="French World",
                language_code="fr",
                available_characters=[
                    "yeti",
                ],
            ),
            character=CharacterContext(
                character_id=character_id,
                name="Yeti",
                personality_reference=(
                    "storyteller"
                ),
                teaching_style=(
                    "narrative learning"
                ),
            ),
            voice=voice,
        )


def test_prepare_voice_call():
    session_service = (
        FakeVoiceCharacterSessionService()
    )

    orchestrator = VoiceCallOrchestrator(
        context_builder=(
            FakeInteractionContextBuilder()
        ),
        session_service=session_service,
    )

    request = VoiceCallRequest(
        learner_id="learner-001",
        world_id="french_world",
        character_id="yeti",
        language_code="fr",
    )

    session = (
        orchestrator.prepare_call(
            request=request
        )
    )

    assert session_service.context is not None

    assert (
        session_service.context.voice.voice_profile
        == "yeti"
    )

    assert (
        session_service.context.voice.language_code
        == "fr"
    )

    assert (
        session_service.context.voice.voice_provider
        == "openai"
    )

    assert isinstance(
        session,
        VoiceCallSession,
    )

    assert session.session_id == (
        "voice-session-001"
    )

    assert session.learner_id == (
        "learner-001"
    )

    assert session.character_id == (
        "yeti"
    )

    assert session.world_id == (
        "french_world"
    )

    assert session.language_code == (
        "fr"
    )



