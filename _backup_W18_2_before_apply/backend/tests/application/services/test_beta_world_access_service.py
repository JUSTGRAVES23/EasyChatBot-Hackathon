from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import pytest

from app.application.services.beta_world_access_service import (
    BetaUserNotEligibleError,
    BetaUserNotFoundError,
    BetaWorldAccessError,
    BetaWorldAccessService,
    CanonicalUserNotFoundError,
)
from app.domain.learning.learner_world_access import (
    ACTIVE,
    BETA,
    LearnerWorldAccess,
)


class FakeBetaUserReader:
    def __init__(self, user: dict | None) -> None:
        self.user = user

    async def get_beta_user(self, user_id: str):
        return self.user


class FakeIdentityReader:
    def __init__(self, user_exists: bool = True) -> None:
        self.user_exists = user_exists
        self.requested_ids: list[UUID] = []

    async def get_user_for_identity(self, user_id: UUID):
        self.requested_ids.append(user_id)
        return object() if self.user_exists else None


class FakeWorld:
    def __init__(self, identifier: str, world_id: UUID | None = None, enabled: bool = True):
        self.identifier = identifier
        self.id = world_id or uuid4()
        self.enabled = enabled


class FakeCatalogue:
    def __init__(self, worlds: tuple[FakeWorld, ...]) -> None:
        self.worlds = worlds

    def list_all(self):
        return self.worlds


class FakeWorldAccess:
    def __init__(self) -> None:
        self.grants: list[tuple[UUID, str, str]] = []
        self.records: dict[str, LearnerWorldAccess] = {}

    async def grant_access(
        self,
        *,
        user_id: UUID,
        world_identifier: str,
        access_source: str = BETA,
        allow_disabled_world: bool = False,
    ) -> LearnerWorldAccess:
        self.grants.append(
            (user_id, world_identifier, access_source)
        )

        existing = self.records.get(world_identifier)
        if existing is not None:
            return existing

        world_id = uuid4()
        access = LearnerWorldAccess.grant(
            user_id=user_id,
            world_id=world_id,
            access_source=access_source,
        )
        self.records[world_identifier] = access
        return access


def run(awaitable):
    return asyncio.run(awaitable)


def make_service(
    *,
    user_id: UUID | None = None,
    email_verified: bool = True,
    beta_approved: bool = True,
    user_exists: bool = True,
    worlds: tuple[FakeWorld, ...] = (),
):
    user_id = user_id or uuid4()

    beta_reader = FakeBetaUserReader(
        {
            "user_id": str(user_id),
            "email": "learner@example.test",
            "email_verified": email_verified,
            "beta_approved": beta_approved,
            "telegram_id": None,
            "active_world_id": None,
        }
    )

    identity_reader = FakeIdentityReader(
        user_exists=user_exists
    )
    catalogue = FakeCatalogue(worlds)
    access = FakeWorldAccess()

    service = BetaWorldAccessService(
        beta_user_reader=beta_reader,
        user_identity_reader=identity_reader,
        world_catalogue=catalogue,
        world_access=access,
    )

    return service, beta_reader, identity_reader, catalogue, access


def test_provision_all_worlds_uses_complete_catalogue_without_hard_coded_ids():
    user_id = uuid4()
    worlds = (
        FakeWorld("arabic"),
        FakeWorld("french", enabled=True),
        FakeWorld("technology", enabled=False),
        FakeWorld("science", enabled=False),
    )

    service, _, identity_reader, _, access = make_service(
        user_id=user_id,
        worlds=worlds,
    )

    result = run(
        service.provision_all_worlds(
            beta_user_id="beta-user-1",
        )
    )

    assert len(result) == 4
    assert [item[1] for item in access.grants] == [
        "arabic",
        "french",
        "technology",
        "science",
    ]
    assert all(item[2] == BETA for item in access.grants)
    assert identity_reader.requested_ids == [user_id]


def test_disabled_worlds_are_included_in_beta_portfolio():
    worlds = (
        FakeWorld("french", enabled=True),
        FakeWorld("german", enabled=False),
    )

    service, _, _, _, access = make_service(worlds=worlds)

    result = run(
        service.provision_all_worlds(
            beta_user_id="beta-user-1",
        )
    )

    assert len(result) == 2
    assert [grant[1] for grant in access.grants] == [
        "french",
        "german",
    ]


def test_provisioning_is_idempotent_at_world_access_boundary():
    worlds = (
        FakeWorld("french"),
        FakeWorld("spanish"),
    )

    service, _, _, _, access = make_service(worlds=worlds)

    first = run(
        service.provision_all_worlds(
            beta_user_id="beta-user-1",
        )
    )
    second = run(
        service.provision_all_worlds(
            beta_user_id="beta-user-1",
        )
    )

    assert len(first) == 2
    assert len(second) == 2
    assert len(access.records) == 2


def test_unverified_beta_user_is_rejected():
    service, beta_reader, _, _, _ = make_service(
        email_verified=False,
    )

    with pytest.raises(
        BetaUserNotEligibleError,
        match="Email must be verified",
    ):
        run(
            service.provision_all_worlds(
                beta_user_id="beta-user-1",
            )
        )


def test_unapproved_beta_user_is_rejected():
    service, _, _, _, _ = make_service(
        beta_approved=False,
    )

    with pytest.raises(
        BetaUserNotEligibleError,
        match="not Beta approved",
    ):
        run(
            service.provision_all_worlds(
                beta_user_id="beta-user-1",
            )
        )


def test_missing_beta_user_is_rejected():
    class MissingBetaUserReader(FakeBetaUserReader):
        async def get_beta_user(self, user_id: str):
            return None

    service, _, identity_reader, catalogue, access = make_service()

    service = BetaWorldAccessService(
        beta_user_reader=MissingBetaUserReader(None),
        user_identity_reader=identity_reader,
        world_catalogue=catalogue,
        world_access=access,
    )

    with pytest.raises(
        BetaUserNotFoundError,
        match="Beta user does not exist",
    ):
        run(
            service.provision_all_worlds(
                beta_user_id="beta-user-1",
            )
        )


def test_canonical_identity_is_required():
    service, _, _, _, _ = make_service(
        user_exists=False,
    )

    with pytest.raises(
        CanonicalUserNotFoundError,
        match="Canonical user does not exist",
    ):
        run(
            service.provision_all_worlds(
                beta_user_id="beta-user-1",
            )
        )


def test_invalid_beta_user_uuid_is_rejected():
    class InvalidUuidReader(FakeBetaUserReader):
        async def get_beta_user(self, user_id: str):
            return {
                "user_id": "not-a-uuid",
                "email_verified": True,
                "beta_approved": True,
            }

    service, _, identity_reader, catalogue, access = make_service()

    service = BetaWorldAccessService(
        beta_user_reader=InvalidUuidReader(None),
        user_identity_reader=identity_reader,
        world_catalogue=catalogue,
        world_access=access,
    )

    with pytest.raises(
        BetaWorldAccessError,
        match="valid canonical UUID",
    ):
        run(
            service.provision_all_worlds(
                beta_user_id="beta-user-1",
            )
        )


def test_empty_catalogue_returns_empty_portfolio():
    service, _, _, _, access = make_service(worlds=())

    result = run(
        service.provision_all_worlds(
            beta_user_id="beta-user-1",
        )
    )

    assert result == ()
    assert access.grants == []
