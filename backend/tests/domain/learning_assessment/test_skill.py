from dataclasses import FrozenInstanceError

import pytest

from app.domain.learning_assessment.skill import SkillDefinition


def test_skill_definition_is_immutable_and_valid() -> None:
    skill = SkillDefinition(
        skill_id="grammar.past_tense",
        world_id="french",
        name="Past tense",
        description="Use and distinguish the principal past-tense forms.",
    )

    assert skill.skill_id == "grammar.past_tense"
    assert skill.world_id == "french"
    assert skill.enabled is True

    with pytest.raises(FrozenInstanceError):
        skill.skill_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("field", ["skill_id", "world_id", "name", "description"])
def test_skill_definition_rejects_empty_required_fields(field: str) -> None:
    values = {
        "skill_id": "skill-1",
        "world_id": "french",
        "name": "Skill",
        "description": "Description",
    }
    values[field] = " "

    with pytest.raises(ValueError, match=f"{field} cannot be empty"):
        SkillDefinition(**values)


def test_skill_definition_rejects_invalid_types() -> None:
    with pytest.raises(TypeError, match="skill_id must be a string"):
        SkillDefinition(
            skill_id=123,  # type: ignore[arg-type]
            world_id="french",
            name="Skill",
            description="Description",
        )

    with pytest.raises(TypeError, match="enabled must be a boolean"):
        SkillDefinition(
            skill_id="skill-1",
            world_id="french",
            name="Skill",
            description="Description",
            enabled="yes",  # type: ignore[arg-type]
        )
