from __future__ import annotations

from backend.app.application.announcements.approval.composition import (
    create_announcement_approval_composition,
)


class FakeService:
    async def approve(self, *, publication_id: str, actor: str):
        raise NotImplementedError


async def allow() -> bool:
    return True


def test_ws23_1_3_composition_reuses_injected_approval_service() -> None:
    service = FakeService()

    composition = create_announcement_approval_composition(
        approval_service=service,
        admin_authorizer=allow,
    )

    assert composition.service is service
    assert composition.router is not None
