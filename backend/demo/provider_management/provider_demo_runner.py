from backend.demo.demo_runner import DemoRunner
from backend.demo.demo_scenarios import PROVIDER_SCENARIO


class ProviderDemoRunner:

    async def run(self):

        return await DemoRunner().run(
            "provider_management",
            PROVIDER_SCENARIO,
        )
