"""
Integration tests for the Flash Deal presentation in the
unified hackathon demonstration.

The test verifies that the real executable demo uses the
FlashDealPresenter and still preserves the discovery,
notification, and commerce journeys.
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


def run_demo() -> subprocess.CompletedProcess[str]:
    """Execute the real hackathon demonstration."""

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


def test_demo_renders_flash_deal_presentation():

    result = run_demo()

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

    assert "## Yeti" in output

    assert (
        "### NEW FIND!"
        in output
    )

    assert "iPhone 17 Pro" in output

    assert (
        "Pro. Beautiful. Powerful."
        in output
    )

    assert "### HIGHLIGHTS" in output

    assert "Pro camera system" in output

    assert (
        "### PRICE"
        in output
    )

    assert (
        "Current price:"
        in output
    )

    assert (
        "Discount:"
        in output
    )

    assert (
        "Savings:"
        in output
    )

    assert (
        "### WHY THIS IS RELEVANT TO YOU"
        in output
    )

    assert (
        "### AVAILABLE FROM"
        in output
    )

    assert "Demo Vendor" in output

    assert "### ACTIONS" in output

    assert "[GET DEAL]" in output

    assert "[MORE INFORMATION]" in output


def test_demo_keeps_character_notification_after_card():

    result = run_demo()

    assert result.returncode == 0

    output = result.stdout

    card_position = output.index(
        "### NEW FIND!"
    )

    notification_position = output.index(
        "CHARACTER NOTIFICATION"
    )

    assert notification_position > card_position

    assert "Yeti:" in output

    assert (
        "Look what I found!"
        in output
    )


def test_demo_keeps_commerce_boundary_after_discovery():

    result = run_demo()

    assert result.returncode == 0

    output = result.stdout

    notification_position = output.index(
        "CHARACTER NOTIFICATION"
    )

    commerce_position = output.index(
        "STEP 5 — COMMERCE ACTION"
    )

    assert commerce_position > notification_position

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


def test_demo_keeps_original_hackathon_readiness_marker():

    result = run_demo()

    assert result.returncode == 0

    output = result.stdout

    assert (
        "Governance -> Intelligence -> Learning -> Evaluation"
        in output
    )

    assert (
        "Governance -> Intelligence -> Learning -> "
        "Evaluation -> Personalised Discovery"
        in output
    )

    assert (
        "HACKATHON DEMO: SUCCESS"
        in output
    )