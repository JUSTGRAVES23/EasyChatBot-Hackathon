"""
Reliability tests for the unified EasyChatBot hackathon demo.

H4.3 — Demo Reliability

These tests verify that the hackathon demonstration:

- starts successfully
- completes within a reasonable time
- does not require external API credentials
- produces the expected final success marker

The test intentionally executes the demo as a separate process,
matching how the hackathon presentation will actually run it.

It does not modify or bypass H1, H2, or H3 validation.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

DEMO_PATH = (
    REPOSITORY_ROOT
    / "examples"
    / "hackathon_demo.py"
)


def _run_demo() -> subprocess.CompletedProcess[str]:
    """
    Execute the unified demo with a bounded runtime.

    A timeout protects CI and the hackathon environment from
    a demo process hanging indefinitely.
    """

    return subprocess.run(
        [
            sys.executable,
            str(DEMO_PATH),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_hackathon_demo_completes_within_timeout():
    """
    Verify that the demo completes within 30 seconds.
    """

    result = _run_demo()

    assert result.returncode == 0, (
        "Hackathon demo did not complete successfully.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )


def test_hackathon_demo_is_self_contained():
    """
    Verify that the deterministic hackathon demonstration
    reaches its expected final state.

    The demo uses controlled providers and therefore should
    not require Parallel, LLM, or other external credentials.
    """

    result = _run_demo()

    assert result.returncode == 0

    assert (
        "Governance check: PASSED"
        in result.stdout
    )

    assert (
        "Overall Score: 1.00"
        in result.stdout
    )

    assert (
        "Status: PASS"
        in result.stdout
    )

    assert (
        "HACKATHON DEMO: SUCCESS"
        in result.stdout
    )

    assert (
        "Governance -> Intelligence -> Learning -> Evaluation"
        in result.stdout
    )


def test_hackathon_demo_script_exists():

    assert DEMO_PATH.exists()
    assert DEMO_PATH.is_file()