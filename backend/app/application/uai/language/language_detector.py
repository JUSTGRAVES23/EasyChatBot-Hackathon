"""
Provider-independent language detection contract.

The detector identifies the language used in user input.
It does not decide the active World or response policy.
"""

from __future__ import annotations

from typing import Protocol


class LanguageDetector(Protocol):
    """
    Contract for detecting the language of user input.

    Implementations may use any approved detection mechanism.
    The application treats the returned language code as
    untrusted data and validates it before using it.
    """

    def detect(self, text: str) -> str:
        """
        Detect the language used in the supplied text.

        Parameters
        ----------
        text:
            User-provided text.

        Returns
        -------
        str
            ISO-style language code.

        Raises
        ------
        Exception
            Implementations may raise a controlled exception
            when detection cannot be performed.
        """