"""
Final end-to-end acceptance test for the EasyChatBot hackathon demo.

This test executes the real hackathon demonstration and verifies
the complete product story:

Governance
    ↓
Live Intelligence
    ↓
Learning
    ↓
Evaluation
    ↓
Personalised Discovery
    ↓
Character Notification
    ↓
Commerce Boundary
    ↓
Vendor Handoff

No real external purchase is performed.
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


def run_demo() -> subprocess.CompletedProcess[str]:
    """Execute the real hackathon demo."""

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


def test_complete_hackathon_demo_succeeds():

    result = run_demo()

    assert result.returncode == 0, (
        "Hackathon demonstration failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    output = result.stdout

    # ------------------------------------------------------------------
    # Governance
    # ------------------------------------------------------------------

    assert "STEP 1 — GOVERNANCE" in output
    assert "Decision: ALLOW" in output
    assert "Governance check: PASSED" in output

    # ------------------------------------------------------------------
    # Live Intelligence
    # ------------------------------------------------------------------

    assert "STEP 2 — LIVE INTELLIGENCE" in output
    assert "Topic: AI Act" in output
    assert "Language: French" in output
    assert "Learner level: B2" in output

    # ------------------------------------------------------------------
    # Learning
    # ------------------------------------------------------------------

    assert "Summary:" in output
    assert "Vocabulary:" in output
    assert "Discussion questions:" in output

    assert "gouvernance" in output
    assert "réglementation" in output

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    assert "STEP 3 — AI QUALITY EVALUATION" in output
    assert "Status: PASS" in output

    # ------------------------------------------------------------------
    # Personalised Discovery
    # ------------------------------------------------------------------

    assert (
        "STEP 4 — PERSONALISED DISCOVERY"
        in output
    )

    assert "## Yeti" in output
    assert "### NEW FIND!" in output
    assert "iPhone 17 Pro" in output
    assert "Pro. Beautiful. Powerful." in output

    assert "### HIGHLIGHTS" in output
    assert "Pro camera system" in output
    assert "High-performance chip" in output

    assert "### PRICE" in output
    assert "Current price:" in output
    assert "Discount:" in output
    assert "Savings:" in output

    assert (
        "### WHY THIS IS RELEVANT TO YOU"
        in output
    )

    assert "### AVAILABLE FROM" in output
    assert "Demo Vendor" in output

    assert "### ACTIONS" in output
    assert "[GET DEAL]" in output
    assert "[MORE INFORMATION]" in output

    # ------------------------------------------------------------------
    # Character notification
    # ------------------------------------------------------------------

    assert "CHARACTER NOTIFICATION" in output
    assert "Yeti:" in output
    assert "Look what I found!" in output

    # ------------------------------------------------------------------
    # Commerce boundary
    # ------------------------------------------------------------------

    assert "STEP 5 — COMMERCE ACTION" in output
    assert "Commerce action: INITIATE_PURCHASE" in output
    assert "Status: REDIRECT" in output
    assert "Approved commerce boundary" in output
    assert "Vendor handoff" in output

    # ------------------------------------------------------------------
    # Payment boundary
    # ------------------------------------------------------------------

    assert (
        "Payment is not executed in the hackathon demo."
        in output
    )

    # ------------------------------------------------------------------
    # Final success
    # ------------------------------------------------------------------

    assert "HACKATHON DEMO: SUCCESS" in output

    assert (
        "Governance -> Intelligence -> Learning -> Evaluation"
        in output
    )

    assert (
        "Governance -> Intelligence -> Learning -> "
        "Evaluation -> Personalised Discovery"
        in output
    )


def test_demo_preserves_correct_execution_order():

    result = run_demo()

    assert result.returncode == 0

    output = result.stdout

    governance = output.index(
        "STEP 1 — GOVERNANCE"
    )

    intelligence = output.index(
        "STEP 2 — LIVE INTELLIGENCE"
    )

    evaluation = output.index(
        "STEP 3 — AI QUALITY EVALUATION"
    )

    discovery = output.index(
        "STEP 4 — PERSONALISED DISCOVERY"
    )

    notification = output.index(
        "CHARACTER NOTIFICATION"
    )

    commerce = output.index(
        "STEP 5 — COMMERCE ACTION"
    )

    success = output.index(
        "HACKATHON DEMO: SUCCESS"
    )

    assert governance < intelligence
    assert intelligence < evaluation
    assert evaluation < discovery
    assert discovery < notification
    assert notification < commerce
    assert commerce < success