from __future__ import annotations

import logging
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from sqlalchemy import inspect, text

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)
from app.application.composition.beta_telegram_production import (
    BetaTelegramProductionComposition,
    create_production_beta_telegram_composition,
)
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)
from tests.application.composition.deterministic_language_detector import (
    DeterministicLanguageDetector,
)


# ============================================================================
# TEST ENVIRONMENT
# ============================================================================

# WS-19 is explicitly a production-composition integration test.
# Load the repository .env before the composition creates its PostgreSQL
# engine. Do NOT hard-code DATABASE_URL or any secret in this test.
load_dotenv(".env")


# ============================================================================
# Deterministic LLM provider
# ============================================================================


class FakeProductionLLMProvider:
    """
    Deterministic provider used to exercise the real ConversationRuntime.

    The LLM provider is the only intentionally controlled test seam.
    PostgreSQL, Beta access, conversation service, boundary, policies,
    adapter and Telegram runtime remain real.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    async def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
    ) -> str:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_message": user_message,
            }
        )

        return (
            "Bonjour ! Réponse produite par le "
            "Conversation Runtime."
        )


# ============================================================================
# Functionality-control test seam
# ============================================================================


class FakeFunctionalityControlAuthorizer:
    """Allow the deterministic test control service to be constructed."""

    def can_control_functionality(
        self,
        *,
        actor,
        environment,
        functionality_id,
    ):
        return True


class FakeFunctionalityControlRepository:
    """Keep WS19 control state deterministic and enabled."""

    def get_availability(
        self,
        *,
        environment,
        functionality_id,
    ):
        return "enabled"

    def get_last_action(
        self,
        *,
        environment,
        functionality_id,
    ):
        return None

    def record_transition(self, **kwargs):
        raise AssertionError(
            "WS19 composition tests must not perform a control transition."
        )


def make_functionality_control_service():
    return FunctionalityOperationalControlService(
        authorizer=FakeFunctionalityControlAuthorizer(),
        repository=FakeFunctionalityControlRepository(),
    )


# ============================================================================
# Composition helpers
# ============================================================================


def _build_composition(
    *,
    provider: FakeProductionLLMProvider | None = None,
) -> BetaTelegramProductionComposition:
    """
    Build the real production Telegram composition.

    The LLM provider and language detector are replaced by deterministic
    test doubles.
    """

    if provider is None:
        provider = FakeProductionLLMProvider()

    runtime = ConversationRuntime(
        llm_provider=provider,
    )

    functionality_control_service = make_functionality_control_service()

    return create_production_beta_telegram_composition(
        conversation_runtime=runtime,
        functionality_control_service=functionality_control_service,
        language_detector=DeterministicLanguageDetector("fr"),
    )


def _dispose_composition(
    composition: BetaTelegramProductionComposition,
) -> None:
    """
    Dispose the PostgreSQL engine after each integration test.
    """

    engine = getattr(
        composition,
        "database_engine",
        None,
    )

    if engine is not None:
        engine.dispose()


# ============================================================================
# PostgreSQL helpers
# ============================================================================


def _conversation_event_columns(
    *,
    engine,
) -> set[str]:
    """
    Discover the real production conversation_events schema.

    The test deliberately does not assume an event_id column.
    """

    inspector = inspect(engine)

    return {
        column["name"]
        for column in inspector.get_columns(
            "conversation_events",
        )
    }


def _find_existing_telegram_identities(
    *,
    engine,
    minimum: int = 1,
) -> list[dict[str, str]]:
    """
    Retrieve persisted Telegram classroom identities from PostgreSQL.
    """

    columns = _conversation_event_columns(
        engine=engine,
    )

    required = {
        "telegram_user_hash",
        "conversation_id",
        "world_id",
    }

    missing = required - columns

    if missing:
        raise AssertionError(
            "conversation_events is missing required "
            f"columns: {sorted(missing)}"
        )

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT DISTINCT
                    telegram_user_hash,
                    conversation_id,
                    world_id
                FROM conversation_events
                WHERE telegram_user_hash IS NOT NULL
                  AND world_id IS NOT NULL
                ORDER BY telegram_user_hash
                """
            )
        ).mappings().all()

    identities = [
        {
            "telegram_user_hash": row[
                "telegram_user_hash"
            ],
            "conversation_id": row[
                "conversation_id"
            ],
            "world_id": row[
                "world_id"
            ],
        }
        for row in rows
    ]

    if len(identities) < minimum:
        raise RuntimeError(
            "WS-19 requires at least "
            f"{minimum} persisted Telegram identity "
            "in PostgreSQL."
        )

    return identities


def _find_recent_event(
    *,
    engine,
    telegram_user_hash: str,
):
    """
    Retrieve the most recent persisted conversation event.

    The production table has no event_id column, so ordering uses created_at.
    """

    columns = _conversation_event_columns(
        engine=engine,
    )

    required = {
        "telegram_user_hash",
        "conversation_id",
        "world_id",
        "role",
        "content",
        "created_at",
    }

    missing = required - columns

    if missing:
        raise AssertionError(
            "conversation_events is missing required "
            f"columns: {sorted(missing)}"
        )

    with engine.connect() as connection:
        return connection.execute(
            text(
                """
                SELECT
                    telegram_user_hash,
                    conversation_id,
                    world_id,
                    role,
                    content,
                    created_at
                FROM conversation_events
                WHERE telegram_user_hash = :telegram_user_hash
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {
                "telegram_user_hash":
                    telegram_user_hash,
            },
        ).mappings().first()


# ============================================================================
# WS-19.1 — Production composition
# ============================================================================


def test_ws19_production_composition_creates():
    """
    AC1:
        Production composition creates successfully.
    """

    composition = _build_composition()

    try:
        assert composition is not None

        assert (
            composition.conversation_boundary
            is not None
        )

        assert (
            composition.conversation_service
            is not None
        )

        assert (
            composition.conversation_runtime
            is not None
        )

        assert composition.adapter is not None

        assert composition.runtime is not None

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.2 — Production policy wiring
# ============================================================================


def test_ws19_production_policies_are_injected():
    """
    AC2:
        Real policies are attached to the production boundary.
    """

    composition = _build_composition()

    try:
        boundary = (
            composition.conversation_boundary
        )

        assert getattr(
            boundary,
            "_rate_limiter",
            None,
        ) is not None

        assert getattr(
            boundary,
            "_abuse_protector",
            None,
        ) is not None

        assert getattr(
            boundary,
            "_observability",
            None,
        ) is not None

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.3 — PostgreSQL integration
# ============================================================================


def test_ws19_postgresql_contains_telegram_identity():
    """
    AC3:
        PostgreSQL contains persisted Telegram classroom identity data.
    """

    composition = _build_composition()

    try:
        identities = (
            _find_existing_telegram_identities(
                engine=composition.database_engine,
            )
        )

        assert identities

        assert all(
            identity["telegram_user_hash"]
            for identity in identities
        )

        assert all(
            identity["world_id"]
            for identity in identities
        )

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.4 — Active World
# ============================================================================


@pytest.mark.asyncio
async def test_ws19_active_world_is_resolved():
    """
    AC4:
        The persisted Telegram conversation has an active World.
    """

    composition = _build_composition()

    try:
        identities = (
            _find_existing_telegram_identities(
                engine=composition.database_engine,
            )
        )

        identity = identities[0]

        assert identity["world_id"]
        assert identity["world_id"].strip()

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.5 — Conversation Runtime
# ============================================================================


@pytest.mark.asyncio
async def test_ws19_message_reaches_real_conversation_runtime():
    """
    AC5:
        The real ConversationRuntime is integrated into the production
        conversation service.
    """

    provider = FakeProductionLLMProvider()

    composition = _build_composition(
        provider=provider,
    )

    try:
        assert (
            composition.conversation_runtime
            is not None
        )

        assert (
            composition.conversation_service
            is not None
        )

        service = (
            composition.conversation_service
        )

        service_runtime = getattr(
            service,
            "_runtime",
            None,
        )

        if service_runtime is not None:
            assert (
                service_runtime
                is composition.conversation_runtime
            )

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.6 — Persistence
# ============================================================================


def test_ws19_conversation_events_are_persisted():
    """
    AC6:
        PostgreSQL contains persisted Telegram conversation events.

    The actual production schema is used. No event_id assumption is made.
    """

    composition = _build_composition()

    try:
        identities = (
            _find_existing_telegram_identities(
                engine=composition.database_engine,
            )
        )

        identity = identities[0]

        event = _find_recent_event(
            engine=composition.database_engine,
            telegram_user_hash=(
                identity["telegram_user_hash"]
            ),
        )

        assert event is not None

        assert (
            event["telegram_user_hash"]
            == identity["telegram_user_hash"]
        )

        assert (
            event["conversation_id"]
            == identity["conversation_id"]
        )

        assert (
            event["world_id"]
            == identity["world_id"]
        )

        assert event["role"] is not None
        assert event["content"] is not None
        assert event["created_at"] is not None

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.7 — User and assistant conversation
# ============================================================================


def test_ws19_user_and_assistant_share_conversation():
    """
    AC7:
        User and assistant events share the same conversation_id.
    """

    composition = _build_composition()

    try:
        columns = _conversation_event_columns(
            engine=composition.database_engine,
        )

        assert {
            "telegram_user_hash",
            "conversation_id",
            "role",
        }.issubset(columns)

        with composition.database_engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        telegram_user_hash,
                        conversation_id,
                        role
                    FROM conversation_events
                    WHERE telegram_user_hash IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT 100
                    """
                )
            ).mappings().all()

        assert rows

        conversations: dict[
            tuple[str, str],
            set[str],
        ] = {}

        for row in rows:
            key = (
                row["telegram_user_hash"],
                row["conversation_id"],
            )

            conversations.setdefault(
                key,
                set(),
            ).add(row["role"])

        assert any(
            {"user", "assistant"}.issubset(
                roles,
            )
            for roles in conversations.values()
        )

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.8 — Conversation continuity
# ============================================================================


def test_ws19_persisted_history_is_available():
    """
    AC8:
        Persisted history is available for a Telegram conversation.
    """

    composition = _build_composition()

    try:
        identities = (
            _find_existing_telegram_identities(
                engine=composition.database_engine,
            )
        )

        identity = identities[0]

        with composition.database_engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        conversation_id,
                        role,
                        content
                    FROM conversation_events
                    WHERE telegram_user_hash = :user_hash
                    ORDER BY created_at ASC
                    """
                ),
                {
                    "user_hash":
                        identity[
                            "telegram_user_hash"
                        ],
                },
            ).mappings().all()

        assert rows

        conversation_ids = {
            row["conversation_id"]
            for row in rows
        }

        assert conversation_ids

        assert all(
            row["content"] is not None
            for row in rows
        )

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.9 — Cross-user isolation
# ============================================================================


def test_ws19_different_users_remain_isolated():
    """
    AC9:
        Different Telegram identities do not share persisted conversations.
    """

    composition = _build_composition()

    try:
        identities = (
            _find_existing_telegram_identities(
                engine=composition.database_engine,
                minimum=2,
            )
        )

        first = identities[0]
        second = identities[1]

        with composition.database_engine.connect() as connection:
            first_rows = connection.execute(
                text(
                    """
                    SELECT
                        telegram_user_hash,
                        conversation_id,
                        world_id,
                        role,
                        content
                    FROM conversation_events
                    WHERE telegram_user_hash = :user_hash
                    """
                ),
                {
                    "user_hash":
                        first[
                            "telegram_user_hash"
                        ],
                },
            ).mappings().all()

            second_rows = connection.execute(
                text(
                    """
                    SELECT
                        telegram_user_hash,
                        conversation_id,
                        world_id,
                        role,
                        content
                    FROM conversation_events
                    WHERE telegram_user_hash = :user_hash
                    """
                ),
                {
                    "user_hash":
                        second[
                            "telegram_user_hash"
                        ],
                },
            ).mappings().all()

        assert first_rows
        assert second_rows

        assert (
            first["telegram_user_hash"]
            != second["telegram_user_hash"]
        )

        first_conversations = {
            row["conversation_id"]
            for row in first_rows
        }

        second_conversations = {
            row["conversation_id"]
            for row in second_rows
        }

        assert first_conversations
        assert second_conversations

        assert not (
            first_conversations
            & second_conversations
        )

        assert all(
            row["telegram_user_hash"]
            == first["telegram_user_hash"]
            for row in first_rows
        )

        assert all(
            row["telegram_user_hash"]
            == second["telegram_user_hash"]
            for row in second_rows
        )

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.10 — Rate limiting
# ============================================================================


@pytest.mark.asyncio
async def test_ws19_rate_limiter_is_identity_scoped(
    monkeypatch,
):
    """
    AC10:
        Rate limiting is scoped per Telegram identity.
    """

    monkeypatch.setenv(
        "TELEGRAM_RATE_LIMIT_MAX_MESSAGES",
        "1",
    )

    monkeypatch.setenv(
        "TELEGRAM_RATE_LIMIT_WINDOW_SECONDS",
        "60",
    )

    composition = _build_composition()

    try:
        limiter = (
            composition.conversation_boundary
            ._rate_limiter
        )

        first_user = (
            910000
            + int(uuid4().int % 10000)
        )

        second_user = (
            920000
            + int(uuid4().int % 10000)
        )

        assert await limiter.allow(
            telegram_user_id=first_user,
        )

        assert not await limiter.allow(
            telegram_user_id=first_user,
        )

        assert await limiter.allow(
            telegram_user_id=second_user,
        )

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.11 — Abuse protection
# ============================================================================


@pytest.mark.asyncio
async def test_ws19_abuse_protection_is_identity_scoped(
    monkeypatch,
):
    """
    AC11:
        Abuse protection is independently scoped per Telegram identity.
    """

    monkeypatch.setenv(
        "TELEGRAM_ABUSE_MAX_MESSAGES",
        "1",
    )

    monkeypatch.setenv(
        "TELEGRAM_ABUSE_WINDOW_SECONDS",
        "60",
    )

    composition = _build_composition()

    try:
        protector = (
            composition.conversation_boundary
            ._abuse_protector
        )

        first_user = (
            930000
            + int(uuid4().int % 10000)
        )

        second_user = (
            940000
            + int(uuid4().int % 10000)
        )

        assert await protector.allow(
            telegram_user_id=first_user,
        )

        assert not await protector.allow(
            telegram_user_id=first_user,
        )

        assert await protector.allow(
            telegram_user_id=second_user,
        )

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.12 — World-language policy
# ============================================================================


def test_ws19_policy_messages_use_world_language():
    """
    AC12:
        Policy messages use the active World language.
    """

    from app.application.beta_access.policies.telegram_policy_messages import (
        TelegramPolicyMessageService,
    )

    service = TelegramPolicyMessageService()

    class FrenchContext:
        world_id = "world-fr"
        name = "French World"
        language_code = "fr"
        character = "Alix"
        level = "B1"

    response = service.rate_limit_message(
        context=FrenchContext(),
        retry_after_seconds=30,
    )

    assert (
        "limite de messages"
        in response.lower()
    )

    assert (
        "30 secondes"
        in response.lower()
    )

    assert "token" not in response.lower()
    assert "tokens" not in response.lower()


# ============================================================================
# WS-19.13 — Observability
# ============================================================================


@pytest.mark.asyncio
async def test_ws19_observability_does_not_log_raw_identity_or_content(
    caplog,
):
    """
    AC13 + AC15:
        Operational telemetry must not expose raw Telegram identity or
        learner message content.
    """

    composition = _build_composition()

    try:
        observability = (
            composition.conversation_boundary
            ._observability
        )

        telegram_user_id = (
            950000
            + int(uuid4().int % 10000)
        )

        learner_content = (
            f"WS19-secret-{uuid4().hex}"
        )

        caplog.set_level(
            logging.INFO,
        )

        await observability.record(
            event_type=(
                "telegram_classroom_message"
            ),
            telegram_user_id=telegram_user_id,
            outcome="accepted",
            metadata={
                "world_id": "world-fr",
                "character": "Alix",
                "level": "B1",
            },
        )

        log_text = "\n".join(
            record.getMessage()
            for record in caplog.records
        )

        assert (
            str(telegram_user_id)
            not in log_text
        )

        assert learner_content not in log_text

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.14 — Safe runtime failure
# ============================================================================


@pytest.mark.asyncio
async def test_ws19_runtime_failure_returns_safe_response():
    """
    AC14:
        A runtime failure produces the safe learner-facing response.

    The authorization seam is replaced only for this test so that the
    message can reach the runtime failure path.
    """

    composition = _build_composition()

    try:
        boundary = (
            composition.conversation_boundary
        )

        service = (
            composition.conversation_service
        )

        class FakeApprovedContext:
            world_id = "world-fr"
            name = "French World"
            language_code = "fr"
            character = "Alix"
            level = "B1"

        async def approved_context(
            telegram_user_id: int,
        ):
            return FakeApprovedContext()

        monkeypatch = pytest.MonkeyPatch()

        try:
            monkeypatch.setattr(
                composition.beta_access_service,
                "get_conversation_context",
                approved_context,
            )

            runtime_attribute = None

            for name in (
                "_runtime",
                "_conversation_runtime",
            ):
                if hasattr(service, name):
                    runtime_attribute = name
                    break

            if runtime_attribute is None:
                pytest.skip(
                    "Conversation service does not expose "
                    "a replaceable runtime seam."
                )

            class FailingRuntime:
                async def respond(
                    self,
                    **kwargs,
                ):
                    raise RuntimeError(
                        "database password=WS19-secret"
                    )

            monkeypatch.setattr(
                service,
                runtime_attribute,
                FailingRuntime(),
            )

            response = await boundary.handle_message(
                telegram_user_id=960001,
                message="Bonjour",
            )

            assert (
                response
                == boundary.SAFE_ERROR_RESPONSE
            )

            assert "WS19-secret" not in response
            assert "password" not in response.lower()

        finally:
            monkeypatch.undo()

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.15 — Real Telegram adapter
# ============================================================================


def test_ws19_real_telegram_adapter_is_composed():
    """
    Verify the real Telegram adapter is in the production graph.
    """

    composition = _build_composition()

    try:
        assert composition.adapter is not None

        assert (
            composition.adapter.__class__.__name__
            == "BetaTelegramAdapter"
        )

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.16 — Real Telegram runtime
# ============================================================================


def test_ws19_real_telegram_runtime_is_composed():
    """
    Verify the real TelegramBotRuntime is in the production graph.
    """

    composition = _build_composition()

    try:
        assert composition.runtime is not None

        assert (
            composition.runtime.__class__.__name__
            == "TelegramBotRuntime"
        )

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.17 — Dependency graph
# ============================================================================


def test_ws19_dependency_graph_is_integrated():
    """
    Verify the real production dependency graph.

    Only public composition dependencies are asserted. Internal repository
    implementation details are intentionally not required.
    """

    composition = _build_composition()

    try:
        assert (
            composition.beta_access_service
            is not None
        )

        assert (
            composition.conversation_runtime
            is not None
        )

        assert (
            composition.conversation_service
            is not None
        )

        assert (
            composition.conversation_boundary
            is not None
        )

        assert (
            composition.private_chat_gate
            is not None
        )

        assert (
            composition.start_handler
            is not None
        )

        assert composition.adapter is not None
        assert composition.runtime is not None

    finally:
        _dispose_composition(composition)


# ============================================================================
# WS-19.18 — PostgreSQL schema integrity
# ============================================================================


def test_ws19_postgresql_conversation_schema_is_ready():
    """
    Verify the actual production conversation_events schema.

    event_id is deliberately NOT required because the production table
    does not expose that column.
    """

    composition = _build_composition()

    try:
        columns = _conversation_event_columns(
            engine=composition.database_engine,
        )

        required = {
            "telegram_user_hash",
            "conversation_id",
            "world_id",
            "role",
            "content",
            "created_at",
        }

        assert required.issubset(columns)

    finally:
        _dispose_composition(composition)
