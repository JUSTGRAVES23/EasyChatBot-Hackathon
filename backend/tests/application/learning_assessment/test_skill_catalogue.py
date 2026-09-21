import pytest

from app.application.learning_assessment.skill_catalogue import (
    DisabledSkillError,
    DuplicateSkillError,
    SkillWorldMismatchError,
    StaticLearningSkillCatalogue,
    UnknownSkillError,
)
from app.domain.learning_assessment.skill import SkillDefinition


def make_skill(
    skill_id: str,
    *,
    world_id: str = "french",
    enabled: bool = True,
) -> SkillDefinition:
    return SkillDefinition(
        skill_id=skill_id,
        world_id=world_id,
        name=skill_id,
        description=f"Description for {skill_id}.",
        enabled=enabled,
    )


def test_get_returns_known_skill() -> None:
    catalogue = StaticLearningSkillCatalogue([make_skill("grammar.past_tense")])

    result = catalogue.get(skill_id="grammar.past_tense")

    assert result is not None
    assert result.skill_id == "grammar.past_tense"


def test_get_returns_none_for_unknown_skill() -> None:
    catalogue = StaticLearningSkillCatalogue([make_skill("grammar.past_tense")])

    assert catalogue.get(skill_id="grammar.present") is None


def test_resolve_requires_world_membership() -> None:
    catalogue = StaticLearningSkillCatalogue(
        [make_skill("grammar.past_tense", world_id="french")]
    )

    result = catalogue.resolve(
        world_id="french",
        skill_id="grammar.past_tense",
    )

    assert result.world_id == "french"


def test_resolve_rejects_unknown_skill() -> None:
    catalogue = StaticLearningSkillCatalogue([])

    with pytest.raises(UnknownSkillError, match="not found"):
        catalogue.resolve(
            world_id="french",
            skill_id="grammar.past_tense",
        )


def test_resolve_rejects_world_skill_mismatch() -> None:
    catalogue = StaticLearningSkillCatalogue(
        [make_skill("grammar.past_tense", world_id="french")]
    )

    with pytest.raises(SkillWorldMismatchError, match="does not belong"):
        catalogue.resolve(
            world_id="german",
            skill_id="grammar.past_tense",
        )


def test_resolve_rejects_disabled_skill() -> None:
    catalogue = StaticLearningSkillCatalogue(
        [make_skill("grammar.past_tense", enabled=False)]
    )

    with pytest.raises(DisabledSkillError, match="disabled"):
        catalogue.resolve(
            world_id="french",
            skill_id="grammar.past_tense",
        )


def test_list_for_world_returns_only_enabled_skills_for_that_world() -> None:
    catalogue = StaticLearningSkillCatalogue(
        [
            make_skill("grammar.present"),
            make_skill("grammar.past"),
            make_skill("grammar.future", enabled=False),
            make_skill("german.grammar", world_id="german"),
        ]
    )

    result = catalogue.list_for_world(world_id="french")

    assert [skill.skill_id for skill in result] == [
        "grammar.present",
        "grammar.past",
    ]


def test_duplicate_skill_ids_are_rejected() -> None:
    with pytest.raises(DuplicateSkillError, match="Duplicate learning skill"):
        StaticLearningSkillCatalogue(
            [
                make_skill("grammar.present"),
                make_skill("grammar.present"),
            ]
        )


@pytest.mark.parametrize(
    ("method", "kwargs", "message"),
    [
        ("get", {"skill_id": " "}, "skill_id cannot be empty"),
        (
            "resolve",
            {"world_id": " ", "skill_id": "grammar.present"},
            "world_id cannot be empty",
        ),
        (
            "resolve",
            {"world_id": "french", "skill_id": " "},
            "skill_id cannot be empty",
        ),
        (
            "list_for_world",
            {"world_id": " "},
            "world_id cannot be empty",
        ),
    ],
)
def test_catalogue_validates_identifiers(method, kwargs, message) -> None:
    catalogue = StaticLearningSkillCatalogue([])

    with pytest.raises(ValueError, match=message):
        getattr(catalogue, method)(**kwargs)
