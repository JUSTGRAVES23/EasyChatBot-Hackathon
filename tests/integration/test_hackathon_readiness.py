"""
Final hackathon readiness checks for EasyChatBot.

H4.4 — Hackathon Readiness

This test verifies that the core hackathon deliverables exist
and that the repository contains the executable demonstrations
for the completed workstreams.

It intentionally does not implement new business logic.

Validated capabilities:

H1 — Live Intelligence
H2 — AI Quality Evaluation
H3 — AI Safety & Governance
H4 — Unified Hackathon Demonstration
"""

from __future__ import annotations

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


REQUIRED_FILES = (
    # H1 — Live Intelligence
    "src/ai_agents/live_intelligence_agent/handler.py",
    "src/providers/search_provider/interface.py",
    "src/providers/search_provider/parallel_adapter.py",
    "backend/providers/parallel/parallel_client.py",

    # H2 — AI Quality Evaluation
    "src/evaluation/models.py",
    "src/evaluation/criteria.py",
    "src/evaluation/engine.py",
    "src/evaluation/deterministic_evaluator.py",
    "src/evaluation/report.py",

    # H3 — Governance
    "src/governance/models.py",
    "src/governance/engine.py",

    # H4 — Demonstration
    "examples/live_challenge_demo.py",
    "examples/evaluation_demo.py",
    "examples/governance_demo.py",
    "examples/hackathon_demo.py",

    # H4 — Integration validation
    "tests/integration/test_live_challenge_flow.py",
    "tests/integration/test_parallel_search_provider.py",
    "tests/integration/test_live_challenge_evaluation.py",
    "tests/integration/test_live_intelligence_governance.py",
    "tests/integration/test_hackathon_demo_flow.py",
    "tests/integration/test_hackathon_demo_reliability.py",
)


def test_required_hackathon_files_exist():
    """
    Verify that all required hackathon deliverables exist.
    """

    missing_files = [
        path
        for path in REQUIRED_FILES
        if not (
            REPOSITORY_ROOT / path
        ).is_file()
    ]

    assert not missing_files, (
        "Hackathon readiness check failed. "
        "Missing required files:\n"
        + "\n".join(
            f" - {path}"
            for path in missing_files
        )
    )


def test_hackathon_demo_exists():

    demo_path = (
        REPOSITORY_ROOT
        / "examples"
        / "hackathon_demo.py"
    )

    assert demo_path.exists()
    assert demo_path.is_file()


def test_hackathon_demo_is_not_empty():

    demo_path = (
        REPOSITORY_ROOT
        / "examples"
        / "hackathon_demo.py"
    )

    content = demo_path.read_text(
        encoding="utf-8"
    )

    assert content.strip()


def test_core_workstream_directories_exist():

    required_directories = (
        "src/evaluation",
        "src/governance",
        "src/providers/search_provider",
        "tests/evaluation",
        "tests/governance",
        "tests/integration",
    )

    missing_directories = [
        path
        for path in required_directories
        if not (
            REPOSITORY_ROOT / path
        ).is_dir()
    ]

    assert not missing_directories, (
        "Missing required hackathon directories:\n"
        + "\n".join(
            f" - {path}"
            for path in missing_directories
        )
    )


def test_hackathon_readiness_marker():

    readiness_statement = (
        "Governance -> Intelligence -> "
        "Learning -> Evaluation"
    )

    demo_path = (
        REPOSITORY_ROOT
        / "examples"
        / "hackathon_demo.py"
    )

    content = demo_path.read_text(
        encoding="utf-8"
    )

    assert readiness_statement in content