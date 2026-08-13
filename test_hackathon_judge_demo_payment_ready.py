"""
Acceptance tests for the Windows-safe judge-facing EasyChatBot demo.

The judge demo now includes the Payment Pass contract. The commerce
assertions therefore validate the current presentation contract:

GET DEAL
    ->
Payment Pass
    ->
READY / DEMO
    ->
No payment executed
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

DEMO_PATH = (
    REPOSITORY_ROOT
    / "examples"
    / "hackathon_judge_demo.py"
)


def run_judge_demo() -> subprocess.CompletedProcess[str]:
    """Execute the real judge-facing demonstration."""

    return subprocess.run(
        [
            sys.executable,
            str(DEMO_PATH),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_judge_demo_succeeds():

    result = run_judge_demo()

    assert result.returncode == 0, (
        "Judge demo failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    output = result.stdout

    assert (
        "EasyChatBot - JUDGE DEMONSTRATION"
        in output
    )

    assert (
        "Discover -> Understand -> Personalise -> "
        "Recommend -> Act"
        in output
    )

    assert "JUDGE DEMO: SUCCESS" in output


def test_judge_demo_contains_all_capabilities():

    result = run_judge_demo()

    assert result.returncode == 0

    output = result.stdout

    assert "1 - GOVERNANCE" in output
    assert "2 - LIVE INTELLIGENCE" in output
    assert "3 - LEARNING" in output
    assert "4 - AI QUALITY EVALUATION" in output
    assert "5 - PERSONALISED DISCOVERY" in output
    assert "6 - CHARACTER DISCOVERY" in output
    assert "7 - FLASH DEAL" in output
    assert "8 - COMMERCE BOUNDARY" in output


def test_judge_demo_shows_personalised_discovery():

    result = run_judge_demo()

    assert result.returncode == 0

    output = result.stdout

    assert "Yeti" in output
    assert "Look what I found!" in output
    assert "iPhone 17 Pro" in output
    assert "Pro. Beautiful. Powerful." in output
    assert "WHY THIS IS RELEVANT TO YOU" in output
    assert "Demo Vendor" in output


def test_judge_demo_shows_commerce_boundary():

    result = run_judge_demo()

    assert result.returncode == 0

    output = result.stdout

    assert "GET DEAL -> vendor handoff" in output

    assert "PAYMENT PASS" in output

    assert "Payment status: READY" in output

    assert "Execution mode: DEMO" in output

    assert "[ PROCEED TO CHECKOUT ]" in output

    assert "No payment has been executed." in output

    assert (
        "Vendor checkout remains outside "
        "the hackathon demo."
        in output
    )

    assert "[PASS] Payment execution: NO" in output

    assert "[PASS] Execution mode: DEMO" in output

    assert "EasyChatBot is not a shop." in output


def test_judge_demo_preserves_execution_order():

    result = run_judge_demo()

    assert result.returncode == 0

    output = result.stdout

    governance = output.index(
        "1 - GOVERNANCE"
    )

    intelligence = output.index(
        "2 - LIVE INTELLIGENCE"
    )

    learning = output.index(
        "3 - LEARNING"
    )

    evaluation = output.index(
        "4 - AI QUALITY EVALUATION"
    )

    discovery = output.index(
        "5 - PERSONALISED DISCOVERY"
    )

    character = output.index(
        "6 - CHARACTER DISCOVERY"
    )

    deal = output.index(
        "7 - FLASH DEAL"
    )

    commerce = output.index(
        "8 - COMMERCE BOUNDARY"
    )

    payment = output.index(
        "PAYMENT PASS"
    )

    success = output.index(
        "JUDGE DEMO: SUCCESS"
    )

    assert governance < intelligence
    assert intelligence < learning
    assert learning < evaluation
    assert evaluation < discovery
    assert discovery < character
    assert character < deal
    assert deal < commerce
    assert commerce < payment
    assert payment < success