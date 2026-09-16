from __future__ import annotations


from datetime import datetime, timezone


import pytest


from app.application.memory.memory_approval_service import (
    MemoryApprovalService,
)


from app.application.memory.memory_candidate import (
    MemoryCandidate,
)


from app.application.memory.memory_policy import (
    MemoryPolicy,
)



def create_service() -> MemoryApprovalService:

    return MemoryApprovalService(
        memory_policy=MemoryPolicy(),
    )



def create_candidate(
    *,
    category: str = "grammar_mistake",
    observation: str = (
        "Learner confuses French past tense structures."
    ),
) -> MemoryCandidate:


    return MemoryCandidate(

        candidate_id="candidate-001",

        learner_hash="learner-hash-001",

        category=category,

        observation=observation,

        confidence=0.85,

        evidence_event_ids=[
            "conversation-event-001"
        ],

        metadata={
            "created_by": "test",
        },

        created_at=datetime.now(
            timezone.utc
        ),

    )



def test_memory_approval_approves_valid_learning_memory():

    service = create_service()


    candidate = create_candidate()


    decision = service.approve(
        candidate
    )


    assert decision["status"] == "approved"


    assert (
        decision["category"]
        ==
        "grammar_mistake"
    )



def test_memory_approval_rejects_personal_information():

    service = create_service()


    candidate = create_candidate(

        observation=(
            "Learner email is "
            "learner@example.com"
        ),

    )


    with pytest.raises(ValueError):

        service.approve(
            candidate
        )



def test_memory_approval_reject_requires_reason():

    service = create_service()


    candidate = create_candidate()


    with pytest.raises(ValueError):

        service.reject(

            candidate,

            reason="",

        )



def test_memory_approval_reject_returns_reason():

    service = create_service()


    candidate = create_candidate()


    decision = service.reject(

        candidate,

        reason="Not educationally relevant.",

    )


    assert decision["status"] == "rejected"

    assert (
        decision["reason"]
        ==
        "Not educationally relevant."
    )
