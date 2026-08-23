from __future__ import annotations


import pytest


from backend.app.application.memory.memory_policy import (
    MemoryPolicy,
)



def test_memory_policy_accepts_learning_memory():

    policy = MemoryPolicy()


    assert policy.validate(

        memory_type="grammar_mistake",

        observation=(
            "Learner often confuses "
            "past tense with avoir."
        ),

    ) is True





def test_memory_policy_rejects_personal_information():

    policy = MemoryPolicy()


    with pytest.raises(ValueError):

        policy.validate(

            memory_type="learning_preference",

            observation=(
                "Learner email is "
                "test@example.com"
            ),

        )





def test_memory_policy_rejects_unknown_memory_type():

    policy = MemoryPolicy()


    with pytest.raises(ValueError):

        policy.validate(

            memory_type="personal_information",

            observation="Some information",

        )