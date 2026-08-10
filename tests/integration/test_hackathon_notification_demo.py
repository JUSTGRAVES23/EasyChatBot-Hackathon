"""
Acceptance test for the character-driven discovery notification
inside the unified hackathon demonstration.

This deliberately executes the real demo as a subprocess.

Expected journey:

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
Commerce Action
    ↓
Vendor Handoff
    ↓
Success
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


def test_hackathon_demo_contains_character_notification():

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
        "Hackathon demo failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    output = result.stdout

    assert (
        "STEP 4 — PERSONALISED DISCOVERY"
        in output
    )

    assert (
        "CHARACTER NOTIFICATION"
        in output
    )

    assert "Yeti:" in output

    assert (
        "Look what I found!"
        in output
    )

    assert "iPhone 17 Pro" in output

    assert (
        "Why this may interest you:"
        in output
    )

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

    assert (
        "Payment is not executed in the hackathon demo."
        in output
    )

    assert (
        "HACKATHON DEMO: SUCCESS"
        in output
    )


def test_hackathon_demo_preserves_readiness_marker():

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

    assert (
        "Governance -> Intelligence -> Learning -> Evaluation"
        in result.stdout
    )