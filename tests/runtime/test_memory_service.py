from backend.memory.memory_service import (
    MemoryService,
)


def test_memory_save_and_recall():

    service = MemoryService()


    service.remember(
        user_id="demo-user",
        category="learning_goal",
        content=(
            "Improve French conversation skills"
        ),
    )


    memories = service.recall(
        "demo-user"
    )


    assert len(memories) == 1


    assert memories[0].content == (
        "Improve French conversation skills"
    )