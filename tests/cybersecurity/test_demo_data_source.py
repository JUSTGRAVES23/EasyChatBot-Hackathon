import pytest

from cybersecurity.demo_data_source import (
    DemoCybersecurityDataSource,
)


@pytest.mark.asyncio
async def test_demo_source_returns_normalized_signals():
    source = DemoCybersecurityDataSource()

    signals = await source.get_signals()

    assert len(signals) == 5
    assert all(signal.source for signal in signals)
    assert all(signal.severity in {"critical", "high", "medium", "low", "info"} for signal in signals)

