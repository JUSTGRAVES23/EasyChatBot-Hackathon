"""
Speech Provider Factory.

Creates speech provider implementations
from configuration.

Responsibilities:
- Convert configuration into providers.
- Centralize provider selection.

Does NOT:
- Execute speech operations.
- Store credentials.
- Manage runtime sessions.
"""

from __future__ import annotations


from app.configuration.providers.speech_provider_config import (
    SpeechProviderConfig,
)


from app.providers.speech.speech_provider import (
    SpeechProvider,
)


from app.providers.speech.openai_speech_provider import (
    OpenAISpeechProvider,
)



class SpeechProviderFactory:
    """
    Factory for speech providers.
    """

    @staticmethod
    def create(
        config: SpeechProviderConfig,
    ) -> SpeechProvider:
        """
        Create speech provider from configuration.

        Parameters
        ----------
        config:
            Provider configuration.

        Returns
        -------
        SpeechProvider
            Configured speech provider.

        Raises
        ------
        ValueError
            If provider is unsupported.
        """

        provider_name = (
            config.provider_name
            .lower()
            .strip()
        )


        if provider_name == "openai":

            return OpenAISpeechProvider()


        raise ValueError(
            f"Unsupported speech provider: {provider_name}"
        )
