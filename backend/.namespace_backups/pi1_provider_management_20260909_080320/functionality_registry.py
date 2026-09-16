from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FunctionalityDefinition:
    functionality_id: str
    name: str
    category: str


FUNCTIONALITIES: tuple[FunctionalityDefinition, ...] = (
    FunctionalityDefinition("conversation", "AI Conversation", "AI"),
    FunctionalityDefinition("telegram", "Telegram", "Communication"),
    FunctionalityDefinition("voice_tts", "Voice / TTS", "AI"),
    FunctionalityDefinition("lessons", "Lessons", "Learning"),
    FunctionalityDefinition("review", "Review / Spaced Repetition", "Learning"),
    FunctionalityDefinition("pdf_presentation", "PDF / Presentation", "Presentation"),
    FunctionalityDefinition("email_workflows", "Email Workflows", "Communication"),
    FunctionalityDefinition("payments", "Payments", "Platform"),
    FunctionalityDefinition("authentication", "Authentication", "Platform"),
    FunctionalityDefinition("scheduler", "Scheduler", "Platform"),
    FunctionalityDefinition("provider_runtime", "Provider / LLM Runtime", "Infrastructure"),
    FunctionalityDefinition("database", "Database", "Infrastructure"),
)


_FUNCTIONALITY_BY_ID = {
    item.functionality_id: item
    for item in FUNCTIONALITIES
}


def get_functionality(functionality_id: str) -> FunctionalityDefinition:
    try:
        return _FUNCTIONALITY_BY_ID[functionality_id]
    except KeyError as exc:
        raise ValueError(
            f"Unknown functionality_id: {functionality_id}"
        ) from exc


def is_known_functionality(functionality_id: str) -> bool:
    return functionality_id in _FUNCTIONALITY_BY_ID
