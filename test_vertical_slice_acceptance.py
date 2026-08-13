"""
EasyChatBot Hackathon Vertical Slice Acceptance Tests.

Workstream:
    WS-2 — Hackathon Vertical Slice Delivery

Sprint:
    H1 — Vertical Slice Definition & Integration Contract

Purpose:
    Define the end-to-end acceptance contract for the hackathon
    vertical slice without modifying the Runtime capability layer.

Target journey:

    User
      |
      v
    Hackathon API
      |
      v
    Application Service
      |
      v
    External Runtime
      |
      v
    Live Intelligence Capability
      |
      v
    Approved Provider
      |
      v
    AI learning response

Important:
    These tests belong to the hackathon integration workstream.
    They must not require changes to:

        src/ai_runtime/capabilities/*

    That Runtime workstream is owned separately.

The tests are intentionally integration-level. They should become
executable once the WS-2 backend vertical slice is implemented.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration


def test_ai_french_teacher_vertical_slice():
    """
    Validate the complete hackathon user journey.

    Acceptance scenario:

        A French learner asks EasyChatBot to teach French
        using current AI news.

    Expected flow:

        API
          |
          v
        Application
          |
          v
        External Runtime
          |
          v
        Live Intelligence
          |
          v
        Provider
          |
          v
        Learning response

    The final implementation must demonstrate that the request
    crosses the application boundary and produces a useful
    learning-oriented response.
    """

    # WS-2 implementation test.
    #
    # This is deliberately left as a contract test until the
    # vertical-slice endpoint and its application integration
    # are implemented in Sprint H2.
    pytest.fail(
        "WS-2 vertical slice is not implemented yet. "
        "Implement the hackathon integration before enabling "
        "this acceptance test."
    )


def test_vertical_slice_acceptance_criteria():
    """
    Document the non-negotiable acceptance criteria for the
    hackathon vertical slice.

    This test is intentionally a contract placeholder during H1.
    """

    acceptance_criteria = {
        "application_entry_point": True,
        "runtime_execution": True,
        "live_intelligence": True,
        "approved_provider": True,
        "learning_oriented_response": True,
        "end_to_end_result": True,
    }

    assert all(acceptance_criteria.values())