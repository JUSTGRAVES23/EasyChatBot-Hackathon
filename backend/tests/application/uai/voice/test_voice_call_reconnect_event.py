"""
Tests for Voice Call Reconnect Event.

Validates:

VoiceCall
      |
      ↓
ACTIVE state
      |
      ↓
Reconnect
      |
      ↓
VoiceCallSession
      |
      ↓
VOICE_CALL_RECONNECTED event


Identity must remain unchanged.
"""


from app.application.uai.voice.voice_call_lifecycle_service import (
    VoiceCallLifecycleService,
)


from app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)


from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)



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


from app.infrastructure.persistence.voice_call_repository import (
    InMemoryVoiceCallRepository,
)


from app.infrastructure.persistence.in_memory_voice_call_event_repository import (
    InMemoryVoiceCallEventRepository,
)



from app.domain.uai.voice.voice_call_event import (
    VoiceCallEventType,
)



def create_service():

    room_service = (
        VoiceRoomService(
            room_adapter=(
                VoiceRoomAdapter()
            ),
        )
    )


    execution_runtime = (
        VoiceCallExecutionRuntime()
    )


    execution_coordinator = (
        VoiceCallExecutionCoordinator(
            room_service=room_service,
            execution_runtime=execution_runtime,
        )
    )


    event_service = (
        VoiceCallEventService(
            repository=(
                InMemoryVoiceCallEventRepository()
            ),
        )
    )


    management_service = (
        VoiceCallManagementService(
            repository=(
                InMemoryVoiceCallRepository()
            ),
        )
    )


    return (
        VoiceCallLifecycleService(
            execution_coordinator=(
                execution_coordinator
            ),

            voice_call_management_service=(
                management_service
            ),

            voice_call_session_service=(
                VoiceCallSessionService()
            ),

            voice_call_event_service=(
                event_service
            ),
        ),

        management_service,
    )



def create_active_voice_call(
    management_service,
):

    voice_call = (
        management_service.create_call(
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
        )
    )


    active_call = (
        voice_call.mark_active()
    )


    management_service.repository.save(
        voice_call=active_call,
    )


    return active_call



def test_reconnect_creates_event():

    service, management_service = (
        create_service()
    )


    voice_call = (
        create_active_voice_call(
            management_service
        )
    )


    session = (
        service.reconnect_call(
            voice_call=voice_call,
        )
    )


    assert session.character_id == (
        "yeti"
    )


    events = (
        service.voice_call_event_service
        .get_events(
            voice_call_id=voice_call.id,
        )
    )


    assert len(events) == 1


    assert events[0].event_type == (
        VoiceCallEventType.RECONNECTED
    )



def test_reconnect_preserves_voice_identity():

    service, management_service = (
        create_service()
    )


    voice_call = (
        create_active_voice_call(
            management_service
        )
    )


    session = (
        service.reconnect_call(
            voice_call=voice_call,
        )
    )


    assert session.learner_id == (
        voice_call.learner_id
    )


    assert session.character_id == (
        voice_call.character_id
    )


    assert session.language_code == (
        voice_call.language_code
    )



def test_reconnect_events_are_isolated():

    service, management_service = (
        create_service()
    )


    first_call = (
        create_active_voice_call(
            management_service
        )
    )


    second_call = (
        management_service.create_call(
            learner_id="learner-002",
            character_id="alix",
            world_id="french_world",
            language_code="fr",
        )
    )


    service.reconnect_call(
        voice_call=first_call,
    )


    events = (
        service.voice_call_event_service
        .get_events(
            voice_call_id=second_call.id,
        )
    )


    assert events == []