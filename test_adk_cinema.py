"""Local smoke test for the Google ADK cinema agent."""

from adk_cinema.agent import root_agent


def main() -> None:
    print("=" * 60)
    print("ADK CINEMA AGENT SMOKE TEST")
    print("=" * 60)

    print(f"Agent: {root_agent.name}")
    print(f"Model: {root_agent.model}")
    print(f"Tools: {len(root_agent.tools)}")

    assert root_agent.name == "easychatbot_cinema_agent"
    assert root_agent.model == "gemini-3.7-flash"
    assert len(root_agent.tools) == 1

    print("\nADK_CINEMA_AGENT_SMOKE_TEST_PASS")


if __name__ == "__main__":
    main()
