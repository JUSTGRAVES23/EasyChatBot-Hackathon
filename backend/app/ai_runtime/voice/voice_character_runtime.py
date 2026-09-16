"""
Voice Character Runtime.

Coordinates character identity
with speech capabilities.

Responsibilities:
- Hold character runtime context.
- Generate character speech requests.
- Preserve personality boundaries.

Does NOT:
- Call providers directly.
- Manage LiveKit.
- Store conversations.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)


from app.domain.uai.context.interaction_context import (
    InteractionContext,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCharacterRuntime:
    """
    Runtime for speaking AI characters.
    """

    context: InteractionContext

    speech_runtime: VoiceSpeechRuntime



    def speak(
        self,
        text: str,
    ) -> bytes:
        """
        Generate character audio.

        Uses the selected character voice profile.
        """

        return self.speech_runtime.synthesize(
            text=text,
            voice_profile=(
                self.context
                .voice
                .voice_profile
            ),
            language_code=(
                self.context
                .voice
                .language_code
            ),
        )



    def character_id(
        self,
    ) -> str:
        """
        Return active character identity.
        """

        return (
            self.context
            .character
            .character_id
        )
