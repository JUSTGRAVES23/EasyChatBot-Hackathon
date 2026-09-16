"""Google ADK cinema intelligence agent."""

from google.adk.agents import Agent

from .tools import run_g5_cinema_workflow


root_agent = Agent(
    name="easychatbot_cinema_agent",
    model="gemini-3.7-flash",
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
