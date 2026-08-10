"""
Acceptance test for the complete personalised discovery journey.

The test verifies the application-level journey:

Memory
    ↓
DiscoveryService
    ↓
FlashDealCard
    ↓
DiscoveryNotification
    ↓
CommerceAction
    ↓
CommerceService
    ↓
Vendor handoff

No real payment is executed.
"""

import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

DEMO_PATH = (
    REPOSITORY_ROOT
    / "examples"
    / "hackathon_demo.py"
)


def test_personalised_discovery_journey_is_demonstrated():

    result = subprocess.run(
        [
            sys.executable,
            str(DEMO_PATH),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "Personalised discovery journey failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    output = result.stdout

    # ---------------------------------------------------------------
    # Discovery
    # ---------------------------------------------------------------

    assert (
        "STEP 4 — PERSONALISED DISCOVERY"
        in output
    )

    assert "iPhone 17 Pro" in output

    assert "Demo Vendor" in output

    # ---------------------------------------------------------------
    # Character notification
    # ---------------------------------------------------------------

    assert (
        "CHARACTER NOTIFICATION"
        in output
    )

    assert "Yeti:" in output

    assert (
        "Look what I found!"
        in output
    )

    assert (
        "Why this may interest you:"
        in output
    )

    # ---------------------------------------------------------------
    # Commerce
    # ---------------------------------------------------------------

    assert (
        "STEP 5 — COMMERCE ACTION"
        in output
    )

    assert (
        "Commerce action: INITIATE_PURCHASE"
        in output
    )

    assert "Status: REDIRECT" in output

    assert (
        "Approved commerce boundary"
        in output
    )

    assert "Vendor handoff" in output

    # ---------------------------------------------------------------
    # Safety boundary
    # ---------------------------------------------------------------

    assert (
        "Payment is not executed in the hackathon demo."
        in output
    )

    # ---------------------------------------------------------------
    # Final result
    # ---------------------------------------------------------------

    assert (
        "HACKATHON DEMO: SUCCESS"
        in output
    )


def test_original_hackathon_capability_flow_remains_intact():

    result = subprocess.run(
        [
            sys.executable,
            str(DEMO_PATH),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0

    output = result.stdout

    assert "STEP 1 — GOVERNANCE" in output

    assert "STEP 2 — LIVE INTELLIGENCE" in output

    assert "STEP 3 — AI QUALITY EVALUATION" in output

    # Preserve the original hackathon readiness contract.
    assert (
        "Governance -> Intelligence -> Learning -> Evaluation"
        in output
    )