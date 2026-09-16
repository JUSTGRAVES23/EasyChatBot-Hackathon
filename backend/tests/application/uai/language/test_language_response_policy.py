"""
Tests for World-aware language response policy.
"""

from dataclasses import dataclass

import pytest

from app.application.uai.language.language_detector import (
    LanguageDetector,
)
from app.application.uai.language.language_response_policy import (
    LanguageResponsePolicy,
)
from app.domain.uai.context.language_policy import (
    LanguagePolicy,
)
from app.domain.uai.context.world_context import (
    WorldContext,
)


SUPPORTED_LANGUAGES = (
    "en",
    "fr",
    "es",
    "pl",
    "de",
    "it",
    "pt",
    "ru",
    "zh",
    "ar",
)


@dataclass
class FakeLanguageDetector:
    detected_language: str
    calls: int = 0
    last_text: str | None = None

    def detect(
        self,
        text: str,
    ) -> str:
        self.calls += 1
        self.last_text = text
        return self.detected_language


class InvalidLanguageDetector:
    def __init__(
        self,
        result,
    ) -> None:
        self.result = result
        self.calls = 0

    def detect(
        self,
        text: str,
    ):
        self.calls += 1
        return self.result


def language_world(
    *,
    world_id: str,
    language_code: str,
) -> WorldContext:
    return WorldContext(
        world_id=world_id,
        name=world_id.replace(
            "_",
            " ",
        ).title(),
        language_code=language_code,
        available_characters=(
            "yeti",
            "alix",
        ),
        world_type="language",
        learning_domain="language_learning",
        language_policy=LanguagePolicy(
            mode=LanguagePolicy.TARGET_LANGUAGE,
            target_language=language_code,
        ),
    )


def domain_world(
    *,
    world_id: str = "cybersecurity_world",
    learning_domain: str = "cybersecurity",
) -> WorldContext:
    return WorldContext(
        world_id=world_id,
        name=world_id.replace(
            "_",
            " ",
        ).title(),
        language_code=None,
        available_characters=(
            "yeti",
            "alix",
        ),
        world_type="domain",
        learning_domain=learning_domain,
        language_policy=LanguagePolicy(
            mode=LanguagePolicy.MIRROR_USER,
            supported_languages=SUPPORTED_LANGUAGES,
        ),
    )


def test_french_world_uses_french():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language="en"
    )

    world = language_world(
        world_id="french_world",
        language_code="fr",
    )

    result = policy.resolve_response_language(
        world=world,
        user_message="Hello, how are you?",
        language_detector=detector,
    )

    assert result == "fr"

    assert detector.calls == 0


def test_polish_world_uses_polish():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language="en"
    )

    world = language_world(
        world_id="polish_world",
        language_code="pl",
    )

    result = policy.resolve_response_language(
        world=world,
        user_message="Hello, how are you?",
        language_detector=detector,
    )

    assert result == "pl"

    assert detector.calls == 0


def test_spanish_world_uses_spanish():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language="fr"
    )

    world = language_world(
        world_id="spanish_world",
        language_code="es",
    )

    result = policy.resolve_response_language(
        world=world,
        user_message="Bonjour.",
        language_detector=detector,
    )

    assert result == "es"

    assert detector.calls == 0


def test_domain_world_mirrors_french():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language="fr"
    )

    world = domain_world()

    result = policy.resolve_response_language(
        world=world,
        user_message="Bonjour, comment allez-vous ?",
        language_detector=detector,
    )

    assert result == "fr"

    assert detector.calls == 1

    assert (
        detector.last_text
        == "Bonjour, comment allez-vous ?"
    )


def test_domain_world_mirrors_chinese():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language="zh"
    )

    world = domain_world()

    result = policy.resolve_response_language(
        world=world,
        user_message="你好，今天怎么样？",
        language_detector=detector,
    )

    assert result == "zh"

    assert detector.calls == 1


def test_domain_world_mirrors_arabic():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language="ar"
    )

    world = domain_world()

    result = policy.resolve_response_language(
        world=world,
        user_message="مرحبا، كيف حالك؟",
        language_detector=detector,
    )

    assert result == "ar"

    assert detector.calls == 1


def test_domain_world_mirrors_each_supported_language():

    policy = LanguageResponsePolicy()

    world = domain_world()

    for language in SUPPORTED_LANGUAGES:

        detector = FakeLanguageDetector(
            detected_language=language
        )

        result = policy.resolve_response_language(
            world=world,
            user_message="Test message.",
            language_detector=detector,
        )

        assert result == language

        assert detector.calls == 1


def test_domain_world_rejects_unsupported_language():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language="nl"
    )

    world = domain_world()

    with pytest.raises(
        ValueError,
        match=(
            "Detected language is not supported "
            "by the active World"
        ),
    ):
        policy.resolve_response_language(
            world=world,
            user_message="Hallo, hoe gaat het?",
            language_detector=detector,
        )

    assert detector.calls == 1


def test_domain_world_rejects_empty_detected_language():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language=" "
    )

    world = domain_world()

    with pytest.raises(
        ValueError,
        match="Detected language cannot be empty.",
    ):
        policy.resolve_response_language(
            world=world,
            user_message="Test message.",
            language_detector=detector,
        )

    assert detector.calls == 1


def test_domain_world_rejects_non_string_detected_language():

    policy = LanguageResponsePolicy()

    detector = InvalidLanguageDetector(
        result=None
    )

    world = domain_world()

    with pytest.raises(
        ValueError,
        match="Detected language must be a string.",
    ):
        policy.resolve_response_language(
            world=world,
            user_message="Test message.",
            language_detector=detector,
        )

    assert detector.calls == 1


def test_domain_world_rejects_empty_user_message():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language="fr"
    )

    world = domain_world()

    with pytest.raises(
        ValueError,
        match="User message cannot be empty.",
    ):
        policy.resolve_response_language(
            world=world,
            user_message=" ",
            language_detector=detector,
        )

    assert detector.calls == 0


def test_target_language_normalizes_language_code():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language="en"
    )

    world = language_world(
        world_id="french_world",
        language_code="FR",
    )

    result = policy.resolve_response_language(
        world=world,
        user_message="Hello.",
        language_detector=detector,
    )

    assert result == "fr"

    assert detector.calls == 0


def test_detected_language_is_normalized():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language=" ZH "
    )

    world = domain_world()

    result = policy.resolve_response_language(
        world=world,
        user_message="你好。",
        language_detector=detector,
    )

    assert result == "zh"

    assert detector.calls == 1


def test_language_policy_is_required():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language="fr"
    )

    world = WorldContext(
        world_id="test_world",
        name="Test World",
        language_code="fr",
    )

    with pytest.raises(
        ValueError,
        match="World language policy is required.",
    ):
        policy.resolve_response_language(
            world=world,
            user_message="Bonjour.",
            language_detector=detector,
        )

    assert detector.calls == 0


def test_detector_cannot_change_active_world():

    policy = LanguageResponsePolicy()

    detector = FakeLanguageDetector(
        detected_language="zh"
    )

    world = domain_world(
        world_id="cybersecurity_world",
    )

    result = policy.resolve_response_language(
        world=world,
        user_message="你好。",
        language_detector=detector,
    )

    assert result == "zh"

    assert world.world_id == (
        "cybersecurity_world"
    )

    assert world.learning_domain == (
        "cybersecurity"
    )


def test_detector_implements_language_detector_protocol():

    detector = FakeLanguageDetector(
        detected_language="fr"
    )

    language_detector: LanguageDetector = detector

    assert language_detector.detect(
        "Bonjour."
    ) == "fr"