from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# EasyChatBot uses backend/ as the Python source root.
# This test is executed from the repository root.
BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


import application.telegram_bootstrap as telegram_bootstrap


class DeterministicLanguageDetector:
    """
    Deterministic test double for the application language-detector
    boundary.

    Production code receives a LanguageDetector through dependency
    injection; this test double deliberately avoids any real language
    detection or external provider.
    """

    def __init__(self, language: str = "en") -> None:
        self.language = language
        self.calls: list[str] = []

    def detect(self, text: str) -> str:
        self.calls.append(text)
        return self.language


@pytest.fixture(autouse=True)
def reset_telegram_bootstrap():
    """
    Keep the module-level Telegram composition isolated between tests.
    """

    telegram_bootstrap.reset_telegram_runtime()

    yield

    telegram_bootstrap.reset_telegram_runtime()


def make_functionality_control_service() -> MagicMock:
    """
    Create a deterministic test double for the application-level
    functionality-control service.
    """

    return MagicMock(
        name="functionality_control_service",
    )


def make_production_composition(
    *,
    runtime: MagicMock,
) -> MagicMock:
    """
    Create the minimal production-composition test double required by
    the Telegram bootstrap boundary.
    """

    composition = MagicMock(
        name="beta_telegram_production_composition",
    )

    composition.beta_telegram.runtime = runtime

    return composition


def test_create_telegram_runtime_requires_language_detector() -> None:
    """
    M2-E.2 regression guard:

    Telegram bootstrap must require an explicitly supplied language
    detector rather than creating a default detector itself.
    """

    functionality_control_service = (
        make_functionality_control_service()
    )

    with pytest.raises(
        ValueError,
        match="language_detector is required.",
    ):
        telegram_bootstrap.create_telegram_runtime(
            functionality_control_service=(
                functionality_control_service
            ),
            language_detector=None,  # type: ignore[arg-type]
        )


def test_create_telegram_runtime_forwards_language_detector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    M2-E.2 regression guard:

    The application-provided language detector must be forwarded
    unchanged to the production Beta Telegram composition.
    """

    functionality_control_service = (
        make_functionality_control_service()
    )

    language_detector = DeterministicLanguageDetector("fr")

    runtime = MagicMock(
        name="telegram_runtime",
    )

    composition = make_production_composition(
        runtime=runtime,
    )

    create_production = MagicMock(
        name="create_production_beta_telegram_composition",
        return_value=composition,
    )

    monkeypatch.setattr(
        telegram_bootstrap,
        "create_production_beta_telegram_composition",
        create_production,
    )

    result = telegram_bootstrap.create_telegram_runtime(
        functionality_control_service=(
            functionality_control_service
        ),
        language_detector=language_detector,
    )

    assert result is runtime

    create_production.assert_called_once()

    call_kwargs = create_production.call_args.kwargs

    assert (
        call_kwargs["functionality_control_service"]
        is functionality_control_service
    )

    assert (
        call_kwargs["language_detector"]
        is language_detector
    )


def test_create_telegram_runtime_reuses_existing_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The production composition is created once and reused by the
    Telegram bootstrap until explicitly reset.
    """

    functionality_control_service = (
        make_functionality_control_service()
    )

    language_detector = DeterministicLanguageDetector("fr")

    runtime = MagicMock(
        name="telegram_runtime",
    )

    composition = make_production_composition(
        runtime=runtime,
    )

    create_production = MagicMock(
        name="create_production_beta_telegram_composition",
        return_value=composition,
    )

    monkeypatch.setattr(
        telegram_bootstrap,
        "create_production_beta_telegram_composition",
        create_production,
    )

    first_runtime = telegram_bootstrap.create_telegram_runtime(
        functionality_control_service=(
            functionality_control_service
        ),
        language_detector=language_detector,
    )

    second_runtime = telegram_bootstrap.create_telegram_runtime(
        functionality_control_service=(
            functionality_control_service
        ),
        language_detector=language_detector,
    )

    assert first_runtime is runtime
    assert second_runtime is runtime

    create_production.assert_called_once()


def test_reset_telegram_runtime_allows_recreation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    reset_telegram_runtime() must clear the active composition so a
    subsequent create call builds a new composition.
    """

    functionality_control_service = (
        make_functionality_control_service()
    )

    language_detector = DeterministicLanguageDetector("fr")

    first_runtime = MagicMock(
        name="first_telegram_runtime",
    )

    second_runtime = MagicMock(
        name="second_telegram_runtime",
    )

    first_composition = make_production_composition(
        runtime=first_runtime,
    )

    second_composition = make_production_composition(
        runtime=second_runtime,
    )

    create_production = MagicMock(
        name="create_production_beta_telegram_composition",
        side_effect=[
            first_composition,
            second_composition,
        ],
    )

    monkeypatch.setattr(
        telegram_bootstrap,
        "create_production_beta_telegram_composition",
        create_production,
    )

    result_one = telegram_bootstrap.create_telegram_runtime(
        functionality_control_service=(
            functionality_control_service
        ),
        language_detector=language_detector,
    )

    telegram_bootstrap.reset_telegram_runtime()

    result_two = telegram_bootstrap.create_telegram_runtime(
        functionality_control_service=(
            functionality_control_service
        ),
        language_detector=language_detector,
    )

    assert result_one is first_runtime
    assert result_two is second_runtime

    assert create_production.call_count == 2


def test_get_telegram_production_composition_requires_creation() -> None:
    """
    Accessing the production composition before bootstrap creation must
    fail explicitly rather than returning an invalid partial object.
    """

    with pytest.raises(
        RuntimeError,
        match=(
            "Telegram production composition has not been created."
        ),
    ):
        telegram_bootstrap.get_telegram_production_composition()