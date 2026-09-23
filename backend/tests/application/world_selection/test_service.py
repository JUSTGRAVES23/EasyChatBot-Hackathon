from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.application.world_selection.service import WorldSelectionService


@dataclass(frozen=True)
class FakeWorld:
    world_id: str


@dataclass(frozen=True)
class FakeUser:
    active_world_id: str | None = None


class FakeCatalogue:
    def __init__(self, worlds: dict[str, FakeWorld]) -> None:
        self.worlds = worlds

    def resolve_runtime_world(self, identifier: str) -> FakeWorld:
        if identifier not in self.worlds:
            raise ValueError(f"Unknown World: {identifier}")
        return self.worlds[identifier]


class FakeBetaAccess:
    def __init__(self, selected_world_id: str = "french_world") -> None:
        self.selected_world_id = selected_world_id
        self.calls: list[tuple[str, str]] = []

    async def assign_world(self, *, user_id: str, world_id: str) -> FakeUser:
        self.calls.append((user_id, world_id))
        return FakeUser(active_world_id=self.selected_world_id)


@pytest.mark.asyncio
async def test_selection_resolves_catalogue_identifier_and_delegates_to_beta_access():
    catalogue = FakeCatalogue({"french": FakeWorld("french_world")})
    beta_access = FakeBetaAccess()

    service = WorldSelectionService(
        world_catalogue=catalogue,
        beta_access=beta_access,
    )

    result = await service.assign_world(
        user_id="user-1",
        world_identifier="french",
    )

    assert result.world_id == "french_world"
    assert beta_access.calls == [("user-1", "french_world")]


@pytest.mark.asyncio
async def test_unknown_catalogue_world_never_calls_beta_access():
    catalogue = FakeCatalogue({})
    beta_access = FakeBetaAccess()

    service = WorldSelectionService(
        world_catalogue=catalogue,
        beta_access=beta_access,
    )

    with pytest.raises(ValueError, match="Unknown World"):
        await service.assign_world(
            user_id="user-1",
            world_identifier="does-not-exist",
        )

    assert beta_access.calls == []
