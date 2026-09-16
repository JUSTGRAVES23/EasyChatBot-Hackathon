import pytest

from app.domain.uai.context.language_policy import (
    LanguagePolicy,
)


def test_target_language_policy_is_valid():
    policy = LanguagePolicy(
        mode=LanguagePolicy.TARGET_LANGUAGE,
        target_language="fr",
    )

    assert policy.mode == "target_language"
    assert policy.target_language == "fr"


def test_mirror_user_policy_is_valid():
    policy = LanguagePolicy(
        mode=LanguagePolicy.MIRROR_USER,
        supported_languages=(
            "en",
            "fr",
            "es",
            "pl",
        ),
    )

    assert policy.mode == "mirror_user"
    assert policy.supported_languages == (
        "en",
        "fr",
        "es",
        "pl",
    )


def test_unknown_policy_mode_is_rejected():
    with pytest.raises(
        ValueError,
        match="Unsupported language policy mode",
    ):
        LanguagePolicy(
            mode="unknown",
        )


def test_target_language_requires_language():
    with pytest.raises(
        ValueError,
        match="target_language is required",
    ):
        LanguagePolicy(
            mode=LanguagePolicy.TARGET_LANGUAGE,
        )


def test_mirror_user_requires_supported_languages():
    with pytest.raises(
        ValueError,
        match="supported_languages are required",
    ):
        LanguagePolicy(
            mode=LanguagePolicy.MIRROR_USER,
        )