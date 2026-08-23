import pytest

from backend.cybersecurity.dashboard_data_source import (
    DashboardCybersecurityDataSource,
)


@pytest.mark.asyncio
async def test_dashboard_cybersecurity_data_source_returns_signals():
    source = DashboardCybersecurityDataSource()

    signals = await source.get_signals()

    assert len(signals) == 4

    assert all(
        signal.status == "open"
        for signal in signals
    )

    signal_ids = {
        signal.signal_id
        for signal in signals
    }

    assert signal_ids == {
        "CYBER-DEMO-001",
        "CYBER-DEMO-002",
        "CYBER-DEMO-003",
        "CYBER-DEMO-004",
    }