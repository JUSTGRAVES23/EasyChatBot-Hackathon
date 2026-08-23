from backend.demo.demo_runner import DemoRunner
from backend.demo.demo_scenarios import CYBERSECURITY_SCENARIO


class CybersecurityDemoRunner:

    async def run(self):

        return await DemoRunner().run(
            "cybersecurity",
            CYBERSECURITY_SCENARIO,
        )
