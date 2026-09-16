"""
Voice Call Management Composition.

Composition root for persistent
voice call management.

Responsibilities:
- Build management service.
- Provide shared repository dependency.

Does NOT:
- Handle HTTP.
- Execute voice calls.
- Manage providers.
"""


from __future__ import annotations


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.application.composition.voice_call_dependencies import (
    voice_call_repository,
)



def create_voice_call_management_service(
) -> VoiceCallManagementService:
    """
    Create configured voice call management service.
    """


    return VoiceCallManagementService(
        repository=(
            voice_call_repository
        ),
    )



def build_voice_call_management_service(
) -> VoiceCallManagementService:
    """
    Dependency builder.
    """


    return (
        create_voice_call_management_service()
    )



__all__ = [
    "create_voice_call_management_service",
    "build_voice_call_management_service",
]




