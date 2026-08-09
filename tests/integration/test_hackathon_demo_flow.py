"""
Integration test for the unified EasyChatBot hackathon demonstration.

Flow:

Governance
    ↓
Live Intelligence
    ↓
Learning Challenge
    ↓
Quality Evaluation
    ↓
Final Result

This test validates the demonstration boundary without
requiring external API calls.

The individual H1, H2 and H3 capabilities remain independently
tested in their own test suites.
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


def test_unified_hackathon_demo_executes_successfully():
    """
    Execute the complete hackathon demonstration as a real
    Python process.

    This validates:
    - repository imports
    - demo entry point
    - governance flow
    - intelligence flow
    - challenge generation
    - evaluation flow
    - final success condition
    """

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
        "Unified hackathon demo failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    assert (
        "HACKATHON DEMO: SUCCESS"
        in result.stdout
    )

    assert (
        "Governance -> Intelligence -> Learning -> Evaluation"
        in result.stdout
    )


def test_unified_demo_file_exists():

    assert DEMO_PATH.exists()

    assert DEMO_PATH.is_file()