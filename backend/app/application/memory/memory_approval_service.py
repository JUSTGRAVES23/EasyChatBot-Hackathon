from __future__ import annotations

import logging

from typing import Any

from app.application.memory.memory_candidate import (
    MemoryCandidate,
)

from app.application.memory.memory_policy import (
    MemoryPolicy,
)


logger = logging.getLogger(__name__)


class MemoryApprovalService:
    """
    Memory governance approval service.

    Responsibilities:

    - validate memory candidates
    - approve educational memories
    - reject unsuitable memories
    - create governance decisions

    Does NOT:

    - persist memory
    - call AI providers
    - modify learner profiles
    - bypass privacy controls

    Beta 1.5.4 boundary:

        MemoryCandidate
              |
              v
        MemoryApprovalService
              |
              v
        MemoryPolicy
              |
              v
        Governance Decision

    Future:

        Approved Candidate
              |
              v
        Domain MemoryItem
    """

    def __init__(
        self,
        *,
        memory_policy: MemoryPolicy,
    ) -> None:

        if memory_policy is None:
            raise ValueError(
                "memory_policy cannot be None."
            )

        self._policy = memory_policy

    def approve(
        self,
        candidate: MemoryCandidate,
    ) -> dict[str, Any]:
        """
        Approve a memory candidate.

        Current Beta behaviour:

        - validates the candidate
        - returns a governance decision
        - does NOT persist memory

        The response intentionally contains both:

        Current Beta fields:
            category
            observation

        Future domain-aligned fields:
            memory_type
            content
        """

        if candidate is None:
            raise ValueError(
                "candidate cannot be None."
            )

        # -------------------------------------------------
        # Normalize candidate fields
        # -------------------------------------------------

        memory_type = (
            candidate.memory_type
            or candidate.category
        )

        content = (
            candidate.content
            or candidate.observation
        )

        learner_id = (
            candidate.learner_id
            or candidate.learner_hash
        )

        confidence_score = (
            candidate.confidence_score
            if candidate.confidence_score is not None
            else candidate.confidence
        )

        source_event_id = (
            candidate.source_event_id
        )

        if (
            source_event_id is None
            and candidate.evidence_event_ids
        ):
            source_event_id = (
                candidate.evidence_event_ids[0]
            )

        # -------------------------------------------------
        # Policy validation
        # -------------------------------------------------

        self._policy.validate(
            memory_type=memory_type,
            content=content,
        )

        # -------------------------------------------------
        # Governance decision
        # -------------------------------------------------

        decision = {
            "status": "approved",

            "candidate_id": (
                candidate.candidate_id
            ),

            # Current Beta contract
            "category": (
                candidate.category
                or memory_type
            ),

            "observation": (
                candidate.observation
                or content
            ),

            # Future domain-aligned contract
            "memory_type": memory_type,

            "content": content,

            "learner_id": learner_id,

            "confidence_score": confidence_score,

            "source_event_id": source_event_id,

            "evidence_event_ids": (
                candidate.evidence_event_ids
                or (
                    [source_event_id]
                    if source_event_id
                    else []
                )
            ),

            "metadata": {
                **(
                    candidate.metadata
                    or {}
                ),
                "approval_status": "approved",
            },
        }

        logger.info(
            "Memory candidate approved id=%s",
            candidate.candidate_id,
        )

        return decision

    def reject(
        self,
        candidate: MemoryCandidate,
        *,
        reason: str,
    ) -> dict[str, Any]:
        """
        Reject a memory candidate.

        Rejection does not:

        - persist memory
        - modify learner data
        - create a MemoryItem

        A governance decision is returned instead.
        """

        if candidate is None:
            raise ValueError(
                "candidate cannot be None."
            )

        if not reason or not reason.strip():
            raise ValueError(
                "Rejection reason required."
            )

        memory_type = (
            candidate.memory_type
            or candidate.category
        )

        learner_id = (
            candidate.learner_id
            or candidate.learner_hash
        )

        source_event_id = (
            candidate.source_event_id
        )

        if (
            source_event_id is None
            and candidate.evidence_event_ids
        ):
            source_event_id = (
                candidate.evidence_event_ids[0]
            )

        decision = {
            "status": "rejected",

            "candidate_id": (
                candidate.candidate_id
            ),

            "learner_id": learner_id,

            # Current Beta contract
            "category": (
                candidate.category
                or memory_type
            ),

            # Future domain-aligned contract
            "memory_type": memory_type,

            "reason": reason.strip(),

            "source_event_id": source_event_id,

            "evidence_event_ids": (
                candidate.evidence_event_ids
                or (
                    [source_event_id]
                    if source_event_id
                    else []
                )
            ),

            "metadata": {
                **(
                    candidate.metadata
                    or {}
                ),
                "approval_status": "rejected",
            },
        }

        logger.info(
            "Memory candidate rejected id=%s",
            candidate.candidate_id,
        )

        return decision
