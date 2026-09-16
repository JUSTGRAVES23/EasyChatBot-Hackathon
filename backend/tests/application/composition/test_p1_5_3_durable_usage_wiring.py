from __future__ import annotations

from unittest.mock import MagicMock

from app.application.composition.beta_telegram_composition import (
    create_beta_telegram_composition,
)
from app.application.providers.provider_usage_capture import (
    ProviderUsageCapture,
)
from src.ai_runtime.providers.usage.repository import ProviderUsageRepository
from tests.application.composition.deterministic_language_detector import (
    DeterministicLanguageDetector,
)


class RecordingRepository(ProviderUsageRepository):
    def __init__(self) -> None:
        self.events = []

    def save(self, event) -> None:
        self.events.append(event)

    def get_all(self):
        return list(self.events)

    def clear(self) -> None:
        self.events.clear()


def test_composition_injects_durable_usage_repository_into_capture() -> None:
    repository = RecordingRepository()
    runtime = MagicMock()

    composition = create_beta_telegram_composition(
        user_repository=MagicMock(),
        token_repository=MagicMock(),
        binding_repository=MagicMock(),
        conversation_event_repository=MagicMock(),
        privacy_identifier_service=MagicMock(),
        conversation_event_validator=MagicMock(),
        conversation_runtime=runtime,
        provider_usage_repository=repository,
        language_detector=DeterministicLanguageDetector(),
    )

    assert composition.provider_usage_repository is repository
    assert composition.conversation_runtime is runtime


def test_default_composition_retains_in_memory_usage_repository() -> None:
    runtime = MagicMock()

    composition = create_beta_telegram_composition(
        user_repository=MagicMock(),
        token_repository=MagicMock(),
        binding_repository=MagicMock(),
        conversation_event_repository=MagicMock(),
        privacy_identifier_service=MagicMock(),
        conversation_event_validator=MagicMock(),
        conversation_runtime=runtime,
        language_detector=DeterministicLanguageDetector(),
    )

    # Explicit runtime injection must not silently create a competing usage
    # repository or alter the injected runtime.
    assert composition.provider_usage_repository is None
    assert composition.conversation_runtime is runtime


def test_provider_usage_repository_is_not_required_for_injected_capture() -> None:
    capture = MagicMock(spec=ProviderUsageCapture)
    runtime = MagicMock()

    composition = create_beta_telegram_composition(
        user_repository=MagicMock(),
        token_repository=MagicMock(),
        binding_repository=MagicMock(),
        conversation_event_repository=MagicMock(),
        privacy_identifier_service=MagicMock(),
        conversation_event_validator=MagicMock(),
        conversation_runtime=runtime,
        provider_usage_capture=capture,
        language_detector=DeterministicLanguageDetector(),
    )

    assert composition.provider_usage_repository is None
    assert composition.conversation_runtime is runtime