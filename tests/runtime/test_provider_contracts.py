import pytest

from backend.providers.base_provider import BaseProvider
from backend.providers.provider_result import ProviderResult
from backend.runtime.context.execution_context import ExecutionContext


class DemoProvider(BaseProvider):

    async def execute(
        self,
        context: ExecutionContext,
    ) -> ProviderResult:

        return ProviderResult(
            success=True,
            provider_id=self.provider_id,
            output="Provider response",
        )


@pytest.mark.asyncio
async def test_provider_execution():

    provider = DemoProvider(
        provider_id="demo_provider"
    )

    context = ExecutionContext(
        user_id="user1",
        request="Generate response"
    )

    result = await provider.execute(context)

    assert result.success is True
    assert result.provider_id == "demo_provider"
    assert result.output == "Provider response"