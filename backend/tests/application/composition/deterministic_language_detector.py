from __future__ import annotations


class DeterministicLanguageDetector:
    """Deterministic test double for the application language-detector contract."""

    def __init__(self, language: str = "en") -> None:
        self.language = language
        self.calls: list[str] = []

    def detect(self, text: str) -> str:
        self.calls.append(text)
        return self.language
