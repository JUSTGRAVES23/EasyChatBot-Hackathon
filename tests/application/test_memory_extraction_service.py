from __future__ import annotations


import pytest


from app.application.memory.memory_extraction_service import (
    MemoryExtractionService,
)


from app.application.memory.memory_policy import (
    MemoryPolicy,
)



def create_service() -> MemoryExtractionService:
    return MemoryExtractionService(
        memory_policy=MemoryPolicy(),
    )



@pytest.mark.asyncio
async def test_memory_extraction_boundary_accepts_conversation_events():

    service = create_service()


    result = await service.extract_candidate(
        conversation_events=[
            {
                "event_id": "event-001",
                "content": (
                    "Learner struggles with "
                    "French past tense."
                ),
            }
        ]
    )


    # Current Beta 1.5.4 behaviour:
    # extraction is not implemented yet.
    #
    # It must not create memory automatically.

    assert result is None



@pytest.mark.asyncio
async def test_memory_extraction_requires_event_collection():

    service = create_service()


    with pytest.raises(TypeError):

        await service.extract_candidate()



@pytest.mark.asyncio
async def test_memory_extraction_does_not_persist_memory():

    service = create_service()


    result = await service.extract_candidate(
        conversation_events=[]
    )


    assert result is None
