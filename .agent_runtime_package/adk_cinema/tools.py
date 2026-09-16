"""Tools exposed to the Google ADK cinema agent."""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from g5_final_hackathon_demo import main as run_g5_demo


async def run_g5_cinema_workflow() -> dict[str, object]:
    """Run the existing G5 workflow through a controlled ADK tool boundary.

    The existing G5 workflow remains authoritative. This adapter does not
    access databases, secrets, providers, or production systems directly.
    """
    output = io.StringIO()

    try:
        with redirect_stdout(output):
            await run_g5_demo()

        text = output.getvalue()

        success = "G5_FINAL_HACKATHON_DEMO_SUCCESS" in text

        return {
            "success": success,
            "result": text,
        }

    except Exception as exc:
        return {
            "success": False,
            "result": f"G5 workflow failed: {exc}",
        }