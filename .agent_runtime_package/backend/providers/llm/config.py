"""
LLM Provider Configuration.

Defines approved provider configuration
for the EasyChatBot hackathon runtime.

Configuration is environment-driven so the
application does not hard-code deployment-specific
provider settings.

Local development supports a .env file located
at the EasyChatBot project root.

For the Hackathon runtime, the project .env file
is authoritative. This prevents stale local shell
environment variables from silently overriding the
configured development credentials.

Future production versions should use an external
secret/configuration management system.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# Resolve the EasyChatBot project root.
#
# config.py:
# backend/
#   providers/
#     llm/
#       config.py
#
# parents[3] -> EasyChatBot-Hackathon/
PROJECT_ROOT = Path(
    __file__
).resolve().parents[3]

ENV_FILE = PROJECT_ROOT / ".env"


# Load the Hackathon project's local configuration.
#
# override=True is intentional for the local Hackathon
# runtime because .env is the authoritative project
# configuration source.
#
# Production deployments must not rely on this mechanism.
load_dotenv(
    dotenv_path=ENV_FILE,
    override=True,
)


DEFAULT_PROVIDER = "openai"

DEFAULT_MODEL = "gpt-5-mini"

DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"


def get_llm_provider_name() -> str:
    """
    Return the configured LLM provider name.

    Environment variable:

        EASYCHATBOT_LLM_PROVIDER

    Default:

        openai

    Returns
    -------
    str
        Normalised provider identifier.

    Raises
    ------
    ValueError
        If the configured provider name is empty.
    """

    provider = os.getenv(
        "EASYCHATBOT_LLM_PROVIDER",
        DEFAULT_PROVIDER,
    )

    provider = provider.strip().lower()

    if not provider:
        raise ValueError(
            "LLM provider name cannot be empty."
        )

    return provider


def get_llm_model() -> str:
    """
    Return the configured model for the
    default/current LLM path.

    Environment variable:

        EASYCHATBOT_LLM_MODEL

    Default:

        gpt-5-mini

    Returns
    -------
    str
        Configured model identifier.

    Raises
    ------
    ValueError
        If the configured model is empty.
    """

    model = os.getenv(
        "EASYCHATBOT_LLM_MODEL",
        DEFAULT_MODEL,
    )

    model = model.strip()

    if not model:
        raise ValueError(
            "LLM model cannot be empty."
        )

    return model


def get_gemini_model() -> str:
    """
    Return the configured Gemini model.

    Environment variable:

        EASYCHATBOT_GEMINI_MODEL

    Default:

        gemini-3.6-flash

    Returns
    -------
    str
        Configured Gemini model identifier.

    Raises
    ------
    ValueError
        If the configured Gemini model is empty.
    """

    model = os.getenv(
        "EASYCHATBOT_GEMINI_MODEL",
        DEFAULT_GEMINI_MODEL,
    )

    model = model.strip()

    if not model:
        raise ValueError(
            "Gemini model cannot be empty."
        )

    return model
