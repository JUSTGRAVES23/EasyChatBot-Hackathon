"""Google ADK cinema intelligence agent."""

from __future__ import annotations

import os
from functools import cached_property

from google import genai
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

from .tools import run_g5_cinema_workflow


class EuGemini(Gemini):
    """Gemini ADK model routed through the Vertex AI EU endpoint.

    Agent Runtime remains deployed in its regional location
    (europe-west1), while Gemini 3.7 Flash is requested through
    the EU multi-region endpoint because that model is not available
    from the europe-west1 publisher endpoint.
    """

    @cached_property
    def api_client(self) -> genai.Client:
        """Create a Vertex AI GenAI client explicitly targeting EU."""
        return genai.Client(
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            location="eu",
        )


root_agent = Agent(
    name="easychatbot_cinema_agent",
    model=EuGemini(model="gemini-3.7-flash"),
    description=(
        "A cinema intelligence agent that uses live research, "
        "Gemini reasoning, learner memory, and personalisation."
    ),
    instruction="""
You are the EasyChatBot Cinema Intelligence Agent.

Your job is to help filmmakers, screenwriters, studio crews,
and other media professionals understand current developments.

When the user asks for current cinema/media intelligence,
use the run_g5_cinema_workflow tool.

Do not invent live information.
Do not claim a workflow succeeded unless the tool reports success.
Present the resulting intelligence clearly and concisely.

The underlying workflow already handles live research,
Gemini reasoning, memory, and personalisation.
""".strip(),
    tools=[run_g5_cinema_workflow],
)