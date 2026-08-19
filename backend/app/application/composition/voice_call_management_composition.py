"""
Voice Call Management Composition.

Composition root for voice call identity management.

Responsibilities:
- Build repository dependencies.
- Provide shared application service.
- Preserve voice call identity lifecycle.

Does NOT:
- Handle HTTP.
- Execute runtime.
- Manage providers.
"""

from __future__ import annotations


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.infrastructure.persistence.voice_call_repository import (
    InMemoryVoiceCallRepository,
)



#
# Application lifetime repository.
#
# Temporary Beta implementation.
#
# Future:
# Replace with PostgreSQL repository.
#

_voice_call_repository = (
    InMemoryVoiceCallRepository()
)



def create_voice_call_management_service(
) -> VoiceCallManagementService:
    """
    Create configured voice call management service.
    """


    return VoiceCallManagementService(
        repository=(
            _voice_call_repository
        ),
    )



def build_voice_call_management_service(
) -> VoiceCallManagementService:
    """
    Dependency provider.

    Returns service using the same
    repository instance.
    """


    return (
        create_voice_call_management_service()
    )



__all__ = [
    "create_voice_call_management_service",
    "build_voice_call_management_service",
]