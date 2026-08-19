"""
Tests for Voice Call Trigger Service.

Validates complete workflow:

Trigger
   |
   ↓
VoiceCall
   |
   ↓
VoiceCallInvitation
   |
   ↓
VoiceCallNotification

The same voice_call_id
must be preserved.
"""

from app.application.uai.voice.voice_call_trigger_service import (
    VoiceCallTriggerService,
)


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
)


from app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)


from app.infrastructure.persistence.voice_call_repository import (
    InMemoryVoiceCallRepository,
)


from app.infrastructure.persistence.in_memory_voice_call_notification_repository import (
    InMemoryVoiceCallNotificationRepository,
)


from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotificationChannel,
)


from app.application.uai.voice.voice_call_invitation_repository import (
    VoiceCallInvitationRepository,
)



class FakeInvitationRepository(
    VoiceCallInvitationRepository,
):

    def __init__(self):
        self.storage = {}



    def save(
        self,
        *,
        invitation,
    ):

        self.storage[
            invitation.id
        ] = invitation

        return invitation



    def get_by_id(
        self,
        *,
        invitation_id,
    ):

        return self.storage.get(
            invitation_id
        )



    def delete(
        self,
        *,
        invitation_id,
    ):

        self.storage.pop(
            invitation_id,
            None,
        )



def create_service():

    return VoiceCallTriggerService(

        voice_call_management_service=(
            VoiceCallManagementService(
                repository=(
                    InMemoryVoiceCallRepository()
                ),
            )
        ),


        voice_call_invitation_service=(
            VoiceCallInvitationService(
                repository=(
                    FakeInvitationRepository()
                ),
            )
        ),


        voice_call_notification_service=(
            VoiceCallNotificationService(
                repository=(
                    InMemoryVoiceCallNotificationRepository()
                ),
            )
        ),
    )



def test_trigger_voice_call_creates_complete_flow():

    service = create_service()


    result = (
        service.trigger_voice_call(
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
            notification_channel=(
                VoiceCallNotificationChannel.INBOX
            ),
        )
    )


    voice_call = result[
        "voice_call"
    ]

    invitation = result[
        "invitation"
    ]

    notification = result[
        "notification"
    ]


    assert voice_call.id


    assert invitation.voice_call_id == (
        voice_call.id
    )


    assert notification.voice_call_id == (
        voice_call.id
    )



def test_trigger_preserves_learner_identity():

    service = create_service()


    result = (
        service.trigger_voice_call(
            learner_id="learner-002",
            character_id="alix",
            world_id="french_world",
            language_code="fr",
            notification_channel=(
                VoiceCallNotificationChannel.EMAIL
            ),
        )
    )


    assert result[
        "voice_call"
    ].learner_id == (
        "learner-002"
    )


    assert result[
        "notification"
    ].learner_id == (
        "learner-002"
    )