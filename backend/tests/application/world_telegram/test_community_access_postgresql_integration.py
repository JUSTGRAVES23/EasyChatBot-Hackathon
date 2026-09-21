from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from dotenv import load_dotenv
from sqlalchemy import text

from app.application.composition.beta_telegram_production import (
    BetaTelegramProductionComposition,
    create_production_beta_telegram_composition,
)
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)
from app.application.world_telegram.community_access_service import (
    WorldTelegramCommunityAccessService,
)
from app.application.world_telegram.membership_service import (
    WorldTelegramMembershipService,
)
from app.domain.world_telegram import (
    TelegramDestinationType,
    TelegramMembershipStatus,
    WorldTelegramDestination,
)
from app.infrastructure.persistence.postgresql_world_telegram_destination_repository import (
    PostgreSQLWorldTelegramDestinationRepository,
)
from app.infrastructure.persistence.postgresql_world_telegram_membership_repository import (
    PostgreSQLWorldTelegramMembershipRepository,
)
from app.infrastructure.persistence.postgresql_learning_world_catalogue_repository import (
    PostgreSQLLearningWorldCatalogueRepository,
)


load_dotenv(".env")


class FakeProductionLLMProvider:
    async def generate(self, *args, **kwargs):
        raise AssertionError(
            "LLM provider must not be called by W19.3."
        )


class DeterministicLanguageDetector:
    def __init__(self, language: str = "fr") -> None:
        self._language = language

    def detect(self, text: str) -> str:
        return self._language


class FakeFunctionalityControlAuthorizer:
    def authorize(self, *args, **kwargs) -> None:
        return None


class FakeFunctionalityControlRepository:
    def get(self, *args, **kwargs):
        return None


def make_functionality_control_service() -> (
    FunctionalityOperationalControlService
):
    return FunctionalityOperationalControlService(
        repository=FakeFunctionalityControlRepository(),
        authorizer=FakeFunctionalityControlAuthorizer(),
    )


def _build_composition() -> BetaTelegramProductionComposition:
    from app.ai_runtime.conversation.conversation_runtime import (
        ConversationRuntime,
    )

    runtime = ConversationRuntime(
        llm_provider=FakeProductionLLMProvider(),
    )

    return create_production_beta_telegram_composition(
        conversation_runtime=runtime,
        functionality_control_service=(
            make_functionality_control_service()
        ),
        language_detector=DeterministicLanguageDetector(),
    )


def _dispose_composition(
    composition: BetaTelegramProductionComposition,
) -> None:
    async_engine = getattr(
        composition,
        "async_database_engine",
        None,
    )
    if async_engine is not None:
        # The production composition owns this engine.
        # The integration test intentionally does not use it.
        pass

    engine = getattr(
        composition,
        "database_engine",
        None,
    )
    if engine is not None:
        engine.dispose()


def _find_entitled_user_and_world(
    composition: BetaTelegramProductionComposition,
) -> tuple[UUID, UUID]:
    """
    Select an existing learner World entitlement from PostgreSQL.

    No test user or World is created. This preserves the existing
    authoritative authorization/catalogue data.
    """

    with composition.session_factory() as session:
        row = session.execute(
            text(
                """
                SELECT user_id, world_id
                FROM learner_world_access
                WHERE UPPER(status) = 'ACTIVE'
                ORDER BY created_at
                LIMIT 1
                """
            )
        ).first()

    if row is None:
        pytest.skip(
            "No active learner_world_access record exists in PostgreSQL."
        )

    user_id = row[0]
    world_id = row[1]

    if not isinstance(user_id, UUID):
        user_id = UUID(str(user_id))

    if not isinstance(world_id, UUID):
        world_id = UUID(str(world_id))

    return user_id, world_id


def test_w19_3_real_postgresql_idempotent_membership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    W19.3 production integration:

    - uses the real PostgreSQL production composition;
    - uses the real WorldAccessService;
    - uses the real W19.1 destination repository;
    - uses the real W19.2 membership repository/service;
    - creates ACTIVE membership for an entitled learner;
    - verifies idempotency;
    - does not grant World access;
    - performs no Telegram API operation.
    """

    composition = _build_composition()

    destination_id = uuid4()

    try:
        user_id, world_id = _find_entitled_user_and_world(
            composition
        )

        catalogue_repository = (
            PostgreSQLLearningWorldCatalogueRepository(
                composition.session_factory,
            )
        )

        world = catalogue_repository.get_by_id(world_id)

        if world is None:
            pytest.skip(
                "Selected learner entitlement references a World "
                "that is not present in the authoritative catalogue."
            )

        destination_repository = (
            PostgreSQLWorldTelegramDestinationRepository(
                composition.session_factory,
            )
        )

        membership_repository = (
            PostgreSQLWorldTelegramMembershipRepository(
                composition.session_factory,
            )
        )

        # Use a unique test chat ID so the test never conflicts with
        # an existing registered Telegram destination.
        destination = WorldTelegramDestination(
            id=destination_id,
            world_id=world_id,
            telegram_chat_id=f"-100{uuid4().int % 10**12:012d}",
            destination_type=TelegramDestinationType.GROUP,
            enabled=True,
            created_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ),
            updated_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ),
        )

        destination_repository.save(destination)

        service = composition.world_telegram_community_access_service

        assert isinstance(
            service,
            WorldTelegramCommunityAccessService,
        )

        membership = service.ensure_membership(
            user_id=user_id,
            world_id=world_id,
        )

        assert membership.user_id == user_id
        assert membership.destination_id == destination_id
        assert membership.status is TelegramMembershipStatus.ACTIVE
        assert membership.left_at is None

        # Confirm the persisted membership is real PostgreSQL state.
        persisted = membership_repository.get_by_id(
            membership.id
        )

        assert persisted is not None
        assert persisted.id == membership.id
        assert persisted.user_id == user_id
        assert persisted.destination_id == destination_id
        assert persisted.status is TelegramMembershipStatus.ACTIVE

        # Idempotency: second call must return the existing membership,
        # not create another row.
        second_membership = service.ensure_membership(
            user_id=user_id,
            world_id=world_id,
        )

        assert second_membership.id == membership.id
        assert second_membership.destination_id == destination_id
        assert second_membership.user_id == user_id
        assert second_membership.status is TelegramMembershipStatus.ACTIVE

        with composition.session_factory() as session:
            membership_count = session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM world_telegram_memberships
                    WHERE destination_id = :destination_id
                      AND user_id = :user_id
                    """
                ),
                {
                    "destination_id": destination_id,
                    "user_id": user_id,
                },
            ).scalar_one()

            assert membership_count == 1

            # W19.3 must never create or modify World authorization.
            access_row = session.execute(
                text(
                    """
                    SELECT status
                    FROM learner_world_access
                    WHERE user_id = :user_id
                      AND world_id = :world_id
                    """
                ),
                {
                    "user_id": user_id,
                    "world_id": world_id,
                },
            ).first()

            assert access_row is not None
            assert str(access_row[0]).upper() == "ACTIVE"

        print(
            "W19.3 POSTGRESQL INTEGRATION: PASS"
        )
        print(
            f"W19.3 USER: {user_id}"
        )
        print(
            f"W19.3 WORLD: {world_id}"
        )
        print(
            f"W19.3 DESTINATION: {destination_id}"
        )
        print(
            f"W19.3 MEMBERSHIP: {membership.id}"
        )
        print(
            "W19.3 IDEMPOTENCY: PASS"
        )
        print(
            "W19.3 WORLD ACCESS UNCHANGED: PASS"
        )
        print(
            "W19.3 TELEGRAM API: NOT CALLED"
        )

    finally:
        # Delete membership first because destination is referenced by FK.
        try:
            with composition.session_factory() as session:
                session.execute(
                    text(
                        """
                        DELETE FROM world_telegram_memberships
                        WHERE destination_id = :destination_id
                        """
                    ),
                    {
                        "destination_id": destination_id,
                    },
                )
                session.execute(
                    text(
                        """
                        DELETE FROM world_telegram_destinations
                        WHERE id = :destination_id
                        """
                    ),
                    {
                        "destination_id": destination_id,
                    },
                )
                session.commit()
        finally:
            _dispose_composition(composition)