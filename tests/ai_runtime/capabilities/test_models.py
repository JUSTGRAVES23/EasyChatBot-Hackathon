"""
Tests for AI Runtime capability contracts.
"""

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityResult,
    CapabilityType,
)


def test_capability_request_accepts_valid_request():

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="req-001",
        payload={
            "topic": "AI Act",
        },
    )

    assert (
        request.capability
        == CapabilityType.LIVE_INTELLIGENCE
    )

    assert request.request_id == "req-001"

    assert request.payload == {
        "topic": "AI Act",
    }

    assert request.requested_by == "application"


def test_capability_request_supports_metadata():

    request = CapabilityRequest(
        capability=CapabilityType.EVALUATION,
        request_id="req-002",
        payload={
            "challenge_id": "challenge-001",
        },
        metadata={
            "trace_id": "trace-001",
        },
        requested_by="learning_application",
    )

    assert request.metadata["trace_id"] == "trace-001"

    assert (
        request.requested_by
        == "learning_application"
    )


def test_empty_request_id_is_rejected():

    try:
        CapabilityRequest(
            capability=CapabilityType.LIVE_INTELLIGENCE,
            request_id="",
            payload={},
        )
    except ValueError as exc:
        assert "request_id" in str(exc)
    else:
        raise AssertionError(
            "Expected empty request_id to be rejected."
        )


def test_empty_requester_is_rejected():

    try:
        CapabilityRequest(
            capability=CapabilityType.LIVE_INTELLIGENCE,
            request_id="req-003",
            payload={},
            requested_by="",
        )
    except ValueError as exc:
        assert "requested_by" in str(exc)
    else:
        raise AssertionError(
            "Expected empty requested_by to be rejected."
        )


def test_capability_result_reports_success():

    result = CapabilityResult(
        request_id="req-004",
        capability=CapabilityType.LIVE_INTELLIGENCE,
        status=CapabilityExecutionStatus.COMPLETED,
        output={
            "summary": "AI Act research",
        },
    )

    assert result.succeeded is True
    assert result.failed is False
    assert result.rejected is False


def test_capability_result_reports_failure():

    result = CapabilityResult(
        request_id="req-005",
        capability=CapabilityType.LIVE_INTELLIGENCE,
        status=CapabilityExecutionStatus.FAILED,
        error="Provider unavailable.",
    )

    assert result.succeeded is False
    assert result.failed is True
    assert result.rejected is False


def test_capability_result_reports_rejection():

    result = CapabilityResult(
        request_id="req-006",
        capability=CapabilityType.LIVE_INTELLIGENCE,
        status=CapabilityExecutionStatus.REJECTED,
        error="Governance policy blocked execution.",
    )

    assert result.succeeded is False
    assert result.failed is False
    assert result.rejected is True


def test_capability_result_preserves_metadata():

    result = CapabilityResult(
        request_id="req-007",
        capability=CapabilityType.EVALUATION,
        status=CapabilityExecutionStatus.ACCEPTED,
        metadata={
            "governance_decision": "allow",
        },
    )

    assert (
        result.metadata["governance_decision"]
        == "allow"
    )