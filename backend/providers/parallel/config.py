"""
Parallel provider configuration.

Secrets are loaded from environment variables.
Never hard-code API keys.
"""

import os


class ParallelConfig:
    """
    Configuration holder for Parallel API.
    """

    @property
    def api_key(self) -> str | None:
        return os.getenv(
            "PARALLEL_API_KEY"
        )