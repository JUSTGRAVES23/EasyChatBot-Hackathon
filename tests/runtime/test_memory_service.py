from memory.memory_service import (
    MemoryService,
)

from memory.memory_store import (
    MemoryStore,
)


def test_memory_save_and_recall(
    tmp_path,
):

    database_path = (
        tmp_path / "memory.db"
    )

    service = MemoryService(
        store=MemoryStore(
            database_path=database_path
        )
    )

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

    assert memories[0].user_id == (
        "demo-user"
    )

    assert memories[0].category == (
        "learning_goal"
    )

    assert memories[0].content == (
        "Improve French conversation skills"
    )
