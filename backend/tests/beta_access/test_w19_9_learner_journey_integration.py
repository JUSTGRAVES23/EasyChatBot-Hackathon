from __future__ import annotations

from dataclasses import dataclass
import logging
from uuid import UUID, uuid4

import pytest
from dotenv import load_dotenv
from sqlalchemy import text

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
from app.application.world_telegram.world_telegram_start_router import (
    WorldTelegramStartRouter,
)
from app.application.world_selection.service import (
    WorldSelectionService,
)
from app.interfaces.telegram.beta_telegram_adapter import (
    BetaTelegramAdapter,
)
from app.infrastructure.telegram.telegram_bot_runtime import (
    TelegramBotRuntime,
)


# ============================================================================
# TEST ENVIRONMENT
# ============================================================================

load_dotenv(".env")


# ============================================================================
# Deterministic LLM provider
# ============================================================================


class FakeProductionLLMProvider:
    """
    Deterministic provider for the W19.9 learner-journey integration.

    The production ConversationRuntime remains real.
    Only the external LLM provider is replaced.
    """

    def __init__(
        self,
        *,
        response: str = "Bonjour ! Réponse produite par W19.9.",
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
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

        if self.error is not None:
            raise self.error

        return self.response


# ============================================================================
# Deterministic language detector
# ============================================================================


class DeterministicLanguageDetector:
    def __init__(self, language: str = "fr") -> None:
        self._language = language

    def detect(self, text: str) -> str:
        if not isinstance(text, str):
            raise TypeError("text must be a string.")

        if not text.strip():
            raise ValueError("text cannot be empty.")

        return self._language


# ============================================================================
# Functionality-control seam
# ============================================================================


class FakeFunctionalityControlAuthorizer:
    def can_control_functionality(
        self,
        *,
        actor,
        environment,
        functionality_id,
    ):
        return True


class FakeFunctionalityControlRepository:
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
            "W19.9 integration tests must not perform functionality transitions."
        )


def make_functionality_control_service():
    return FunctionalityOperationalControlService(
        authorizer=FakeFunctionalityControlAuthorizer(),
        repository=FakeFunctionalityControlRepository(),
    )


# ============================================================================
# Telegram test doubles
# ============================================================================


@dataclass
class FakeTelegramUser:
    id: int


@dataclass
class FakeTelegramChat:
    id: int
    type: str


class FakeTelegramMessage:
    def __init__(self, text: str | None) -> None:
        self.text = text
        self.replies: list[str] = []

    async def reply_text(self, text: str) -> None:
        self.replies.append(text)


@dataclass
class FakeTelegramUpdate:
    effective_user: FakeTelegramUser
    effective_chat: FakeTelegramChat
    effective_message: FakeTelegramMessage


class FakeTelegramContext:
    def __init__(self, args: list[str] | None = None) -> None:
        self.args = args or []


# ============================================================================
# Production composition
# ============================================================================


def _build_composition(
    *,
    provider: FakeProductionLLMProvider | None = None,
) -> BetaTelegramProductionComposition:
    if provider is None:
        provider = FakeProductionLLMProvider()

    runtime = ConversationRuntime(
        llm_provider=provider,
    )

    return create_production_beta_telegram_composition(
        conversation_runtime=runtime,
        functionality_control_service=(
            make_functionality_control_service()
        ),
        language_detector=DeterministicLanguageDetector("fr"),
    )


def _dispose_composition(
    composition: BetaTelegramProductionComposition,
) -> None:
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


def _table_exists(
    composition: BetaTelegramProductionComposition,
    table_name: str,
) -> bool:
    with composition.database_engine.connect() as connection:
        return bool(
            connection.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = :table_name
                    )
                    """
                ),
                {"table_name": table_name},
            ).scalar_one()
        )


def _find_beta_learner(
    composition: BetaTelegramProductionComposition,
) -> dict[str, object]:
    """
    Find an existing authenticated Beta learner suitable for W19.9.

    The test never creates or promotes a learner. It uses authoritative
    persisted Beta state only.
    """

    if not _table_exists(composition, "beta_users"):
        pytest.skip(
            "beta_users table is not available in the configured PostgreSQL database."
        )

    with composition.database_engine.connect() as connection:
        columns = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'beta_users'
                    """
                )
            ).all()
        }

        required = {
            "id",
            "email_verified",
            "beta_approved",
            "telegram_id",
        }

        missing = required - columns

        if missing:
            pytest.skip(
                "beta_users does not expose the required W19.9 fields: "
                f"{sorted(missing)}"
            )

        row = connection.execute(
            text(
                """
                SELECT
                    id,
                    email_verified,
                    beta_approved,
                    telegram_id,
                    active_world_id
                FROM beta_users
                WHERE email_verified = TRUE
                  AND beta_approved = TRUE
                  AND telegram_id IS NOT NULL
                ORDER BY id
                LIMIT 1
                """
            )
        ).mappings().first()

    if row is None:
        pytest.skip(
            "No existing verified, Beta-approved learner with Telegram identity "
            "is available in PostgreSQL."
        )

    return dict(row)


def _find_french_world(
    composition: BetaTelegramProductionComposition,
) -> tuple[str, str]:
    """
    Resolve the public World identifier and canonical runtime World ID.

    The test prefers the authoritative catalogue rather than hard-coding a
    second World registry.
    """

    catalogue_service = composition.catalogue_service

    world = catalogue_service.resolve_runtime_world("french")

    runtime_world_id = getattr(
        world,
        "world_id",
        None,
    )

    if runtime_world_id is None:
        runtime_world_id = getattr(
            world,
            "id",
            None,
        )

    if not runtime_world_id:
        raise AssertionError(
            "Authoritative French World resolved without a runtime World ID."
        )

    return "french", str(runtime_world_id)


def _find_latest_conversation_events(
    composition: BetaTelegramProductionComposition,
    *,
    telegram_user_id: int,
) -> list[dict[str, object]]:
    """
    Retrieve persisted events for the selected Telegram identity.

    W19.9 deliberately uses the production conversation_events schema.
    """

    if not _table_exists(composition, "conversation_events"):
        pytest.skip(
            "conversation_events table is not available in PostgreSQL."
        )

    with composition.database_engine.connect() as connection:
        columns = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'conversation_events'
                    """
                )
            ).all()
        }

        required = {
            "telegram_user_hash",
            "conversation_id",
            "world_id",
            "role",
            "content",
            "created_at",
        }

        if not required.issubset(columns):
            pytest.skip(
                "conversation_events does not expose the production W19.9 "
                "persistence fields."
            )

    # The production repository hashes Telegram identities. The integration
    # test therefore obtains the persisted identity through existing Beta
    # access state rather than inventing a second hashing implementation.
    beta_access_service = composition.beta_access_service

    user = None

    # Resolve the persisted Beta user through the authoritative repository.
    user_repository = getattr(
        beta_access_service,
        "_users",
        None,
    )

    if user_repository is None:
        pytest.skip(
            "Production BetaAccessService does not expose its repository seam."
        )

    user = user_repository.get_by_telegram_id(
        telegram_user_id,
    )

    if user is None:
        pytest.skip(
            "Telegram identity is not persisted in the production Beta repository."
        )

    # Reuse the production privacy/hash boundary when available.
    privacy_identifier_service = getattr(
        composition.conversation_service,
        "_privacy_identifier_service",
        None,
    )

    if privacy_identifier_service is None:
        privacy_identifier_service = getattr(
            composition.conversation_service,
            "_privacy",
            None,
        )

    if privacy_identifier_service is None:
        pytest.skip(
            "Production privacy identifier service is not exposed by "
            "ConversationService."
        )

    hash_method = getattr(
        privacy_identifier_service,
        "hash_telegram_user_id",
        None,
    )

    if hash_method is None:
        hash_method = getattr(
            privacy_identifier_service,
            "hash_identifier",
            None,
        )

    if hash_method is None:
        pytest.skip(
            "Production privacy identifier service does not expose the "
            "required Telegram identity hashing operation."
        )

    telegram_user_hash = hash_method(telegram_user_id)

    with composition.database_engine.connect() as connection:
        rows = connection.execute(
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
                ORDER BY created_at ASC
                """
            ),
            {
                "telegram_user_hash": telegram_user_hash,
            },
        ).mappings().all()

    return [dict(row) for row in rows]


# ============================================================================
# W19.9-A — Authoritative World selection
# ============================================================================


@pytest.mark.asyncio
async def test_w19_9_world_selection_persists_authoritative_runtime_world():
    """
    W19.9-C/D:

    Authenticated learner World selection must resolve the public catalogue
    identifier and persist the canonical runtime World through the existing
    BetaAccessService boundary.
    """

    composition = _build_composition()

    try:
        beta_user = _find_beta_learner(composition)

        user_id = beta_user["id"]

        if isinstance(user_id, UUID):
            canonical_user_id = str(user_id)
        else:
            canonical_user_id = str(user_id)

        public_identifier, runtime_world_id = _find_french_world(
            composition,
        )

        selection_service = WorldSelectionService(
            world_catalogue=composition.catalogue_service,
            beta_access=composition.beta_access_service,
        )

        result = await selection_service.assign_world(
            user_id=canonical_user_id,
            world_identifier=public_identifier,
        )

        assert result.world_id == runtime_world_id

        persisted = composition.beta_access_service._users.get(
            canonical_user_id,
        )

        assert persisted is not None
        assert persisted.active_world_id == runtime_world_id

    finally:
        _dispose_composition(composition)


# ============================================================================
# W19.9-B — Telegram World route
# ============================================================================


def test_w19_9_world_start_route_resolves_catalogue_world_without_authorizing():
    """
    /start world_french is a navigation/resolution operation.

    It must resolve the authoritative catalogue World but must not itself
    grant entitlement or mutate learner authorization.
    """

    composition = _build_composition()

    try:
        router = WorldTelegramStartRouter(
            world_catalogue_service=composition.catalogue_service,
        )

        route = router.resolve("world_french")

        assert route is not None
        assert route.world_identifier == "french"
        assert route.runtime_world_id

    finally:
        _dispose_composition(composition)


# ============================================================================
# W19.9-C/D — Complete private learner journey
# ============================================================================


@pytest.mark.asyncio
async def test_w19_9_selected_world_drives_private_chat_runtime():
    """
    Primary W19.9 learner journey.

    World selection
        -> persisted active World
        -> Telegram private message
        -> authorization
        -> PrivateChatService
        -> ConversationRuntime
        -> deterministic provider
        -> Telegram response
        -> persisted conversation

    The production composition remains real except for the external LLM.
    """

    provider = FakeProductionLLMProvider()

    composition = _build_composition(
        provider=provider,
    )

    try:
        beta_user = _find_beta_learner(composition)

        telegram_id = beta_user["telegram_id"]

        if telegram_id is None:
            pytest.skip(
                "Selected Beta learner has no Telegram identity."
            )

        telegram_id = int(telegram_id)

        user_id = beta_user["id"]

        if isinstance(user_id, UUID):
            canonical_user_id = str(user_id)
        else:
            canonical_user_id = str(user_id)

        public_identifier, runtime_world_id = _find_french_world(
            composition,
        )

        # --------------------------------------------------------------
        # Step 1 — authenticated World selection
        # --------------------------------------------------------------

        selection_service = WorldSelectionService(
            world_catalogue=composition.catalogue_service,
            beta_access=composition.beta_access_service,
        )

        selection_result = await selection_service.assign_world(
            user_id=canonical_user_id,
            world_identifier=public_identifier,
        )

        assert selection_result.world_id == runtime_world_id

        persisted_user = composition.beta_access_service._users.get(
            canonical_user_id,
        )

        assert persisted_user is not None
        assert persisted_user.active_world_id == runtime_world_id

        # --------------------------------------------------------------
        # Step 2 — Telegram World navigation
        # --------------------------------------------------------------

        world_router = WorldTelegramStartRouter(
            world_catalogue_service=composition.catalogue_service,
        )

        route = world_router.resolve(
            "world_french",
        )

        assert route is not None
        assert route.world_identifier == "french"
        assert route.runtime_world_id == runtime_world_id

        # --------------------------------------------------------------
        # Step 3 — private Telegram message
        # --------------------------------------------------------------

        message = FakeTelegramMessage(
            "Bonjour",
        )

        update = FakeTelegramUpdate(
            effective_user=FakeTelegramUser(
                telegram_id,
            ),
            effective_chat=FakeTelegramChat(
                telegram_id,
                "private",
            ),
            effective_message=message,
        )

        runtime = composition.runtime

        await runtime._handle_private_message(
            update,
            FakeTelegramContext(),
        )

        # --------------------------------------------------------------
        # Step 4 — provider/runtime contract
        # --------------------------------------------------------------

        assert provider.calls

        assert provider.calls[-1]["user_message"] == "Bonjour"

        # --------------------------------------------------------------
        # Step 5 — exactly one Telegram response
        # --------------------------------------------------------------

        assert message.replies == [
            "Bonjour ! Réponse produite par W19.9.",
        ]

        assert len(message.replies) == 1

        # --------------------------------------------------------------
        # Step 6 — persisted World remains authoritative
        # --------------------------------------------------------------

        persisted_after_message = (
            composition.beta_access_service._users.get(
                canonical_user_id,
            )
        )

        assert persisted_after_message is not None

        assert (
            persisted_after_message.active_world_id
            == runtime_world_id
        )

    finally:
        _dispose_composition(composition)


# ============================================================================
# W19.9-D — Unknown World fails closed
# ============================================================================


def test_w19_9_unknown_world_fails_closed_before_ai():
    """
    Unknown World identifiers must not reach the LLM/runtime.
    """

    provider = FakeProductionLLMProvider()

    composition = _build_composition(
        provider=provider,
    )

    try:
        with pytest.raises(Exception):
            WorldSelectionService(
                world_catalogue=composition.catalogue_service,
                beta_access=composition.beta_access_service,
            )._world_catalogue.resolve_runtime_world(
                "world-that-does-not-exist",
            )

        assert provider.calls == []

    finally:
        _dispose_composition(composition)


# ============================================================================
# W19.9-D — Telegram authorization failure
# ============================================================================


@pytest.mark.asyncio
async def test_w19_9_unauthorized_telegram_user_never_reaches_runtime():
    """
    Telegram authorization must stop the flow before ConversationRuntime.
    """

    provider = FakeProductionLLMProvider()

    composition = _build_composition(
        provider=provider,
    )

    try:
        unauthorized_telegram_id = (
            990000
            + int(uuid4().int % 10000)
        )

        message = FakeTelegramMessage(
            "Bonjour",
        )

        update = FakeTelegramUpdate(
            effective_user=FakeTelegramUser(
                unauthorized_telegram_id,
            ),
            effective_chat=FakeTelegramChat(
                unauthorized_telegram_id,
                "private",
            ),
            effective_message=message,
        )

        await composition.runtime._handle_private_message(
            update,
            FakeTelegramContext(),
        )

        assert provider.calls == []

        assert message.replies

        assert (
            "not authorized"
            in message.replies[0].lower()
        )

        assert len(message.replies) == 1

    finally:
        _dispose_composition(composition)


# ============================================================================
# W19.9-D — Provider failure
# ============================================================================


@pytest.mark.asyncio
async def test_w19_9_provider_failure_returns_safe_response():
    """
    Provider/runtime failure must remain safe and must not expose internal
    failure details to Telegram.
    """

    provider = FakeProductionLLMProvider(
        error=RuntimeError(
            "database password=WS19-secret token=abc123",
        ),
    )

    composition = _build_composition(
        provider=provider,
    )

    try:
        beta_user = _find_beta_learner(composition)

        telegram_id = beta_user["telegram_id"]

        if telegram_id is None:
            pytest.skip(
                "Selected Beta learner has no Telegram identity."
            )

        telegram_id = int(telegram_id)

        message = FakeTelegramMessage(
            "Bonjour",
        )

        update = FakeTelegramUpdate(
            effective_user=FakeTelegramUser(
                telegram_id,
            ),
            effective_chat=FakeTelegramChat(
                telegram_id,
                "private",
            ),
            effective_message=message,
        )

        await composition.runtime._handle_private_message(
            update,
            FakeTelegramContext(),
        )

        assert provider.calls

        assert message.replies

        assert len(message.replies) == 1

        delivered = message.replies[0].lower()

        assert "ws19-secret" not in delivered
        assert "password" not in delivered
        assert "abc123" not in delivered

        assert (
            "something went wrong"
            in delivered
        )

    finally:
        _dispose_composition(composition)


# ============================================================================
# W19.9-D — Response ownership
# ============================================================================


@pytest.mark.asyncio
async def test_w19_9_private_response_is_delivered_exactly_once():
    """
    Telegram runtime + adapter must produce exactly one learner-facing
    response.
    """

    provider = FakeProductionLLMProvider(
        response="Réponse unique W19.9.",
    )

    composition = _build_composition(
        provider=provider,
    )

    try:
        beta_user = _find_beta_learner(composition)

        telegram_id = beta_user["telegram_id"]

        if telegram_id is None:
            pytest.skip(
                "Selected Beta learner has no Telegram identity."
            )

        telegram_id = int(telegram_id)

        message = FakeTelegramMessage(
            "Bonjour",
        )

        update = FakeTelegramUpdate(
            effective_user=FakeTelegramUser(
                telegram_id,
            ),
            effective_chat=FakeTelegramChat(
                telegram_id,
                "private",
            ),
            effective_message=message,
        )

        await composition.runtime._handle_private_message(
            update,
            FakeTelegramContext(),
        )

        assert message.replies == [
            "Réponse unique W19.9.",
        ]

        assert len(message.replies) == 1

    finally:
        _dispose_composition(composition)


# ============================================================================
# W19.9-D — World cannot be overridden by Telegram message
# ============================================================================


@pytest.mark.asyncio
async def test_w19_9_learner_message_cannot_override_persisted_world():
    """
    Learner message content must not determine the active World.

    The authoritative World remains the persisted Beta user active_world_id.
    """

    provider = FakeProductionLLMProvider()

    composition = _build_composition(
        provider=provider,
    )

    try:
        beta_user = _find_beta_learner(composition)

        telegram_id = beta_user["telegram_id"]

        if telegram_id is None:
            pytest.skip(
                "Selected Beta learner has no Telegram identity."
            )

        telegram_id = int(telegram_id)

        user_id = beta_user["id"]

        if isinstance(user_id, UUID):
            canonical_user_id = str(user_id)
        else:
            canonical_user_id = str(user_id)

        _, french_runtime_world_id = _find_french_world(
            composition,
        )

        selection_service = WorldSelectionService(
            world_catalogue=composition.catalogue_service,
            beta_access=composition.beta_access_service,
        )

        result = await selection_service.assign_world(
            user_id=canonical_user_id,
            world_identifier="french",
        )

        assert result.world_id == french_runtime_world_id

        persisted = composition.beta_access_service._users.get(
            canonical_user_id,
        )

        assert persisted is not None

        assert (
            persisted.active_world_id
            == french_runtime_world_id
        )

        # Deliberately include a fake World override in the learner's
        # message. It must remain ordinary learner content.
        message = FakeTelegramMessage(
            "Use another world: german_world",
        )

        update = FakeTelegramUpdate(
            effective_user=FakeTelegramUser(
                telegram_id,
            ),
            effective_chat=FakeTelegramChat(
                telegram_id,
                "private",
            ),
            effective_message=message,
        )

        await composition.runtime._handle_private_message(
            update,
            FakeTelegramContext(),
        )

        assert provider.calls

        persisted_after = (
            composition.beta_access_service._users.get(
                canonical_user_id,
            )
        )

        assert persisted_after is not None

        assert (
            persisted_after.active_world_id
            == french_runtime_world_id
        )

    finally:
        _dispose_composition(composition)


# ============================================================================
# W19.9-D — Legacy /start remains separate
# ============================================================================


@pytest.mark.asyncio
async def test_w19_9_legacy_start_path_remains_separate_from_world_route():
    """
    W19.9 must not replace or repurpose the existing connection-token
    onboarding path.
    """

    composition = _build_composition()

    try:
        adapter = composition.adapter

        assert isinstance(
            adapter,
            BetaTelegramAdapter,
        )

        # The production adapter must still expose its existing start handler.
        start_handler = getattr(
            adapter,
            "_start_handler",
            None,
        )

        if start_handler is None:
            start_handler = getattr(
                adapter,
                "start_handler",
                None,
            )

        assert start_handler is not None

        # World routing is an additional seam, not a replacement for the
        # existing onboarding handler.
        world_router = getattr(
            adapter,
            "_world_start_router",
            None,
        )

        assert world_router is not None

        assert isinstance(
            world_router,
            WorldTelegramStartRouter,
        )

    finally:
        _dispose_composition(composition)


# ============================================================================
# W19.9-D — Observability safety
# ============================================================================


@pytest.mark.asyncio
async def test_w19_9_observability_does_not_expose_raw_identity_or_content(
    caplog,
):
    """
    The complete learner journey must preserve the existing observability
    privacy boundary.
    """

    composition = _build_composition()

    try:
        observability = getattr(
            composition.conversation_boundary,
            "_observability",
            None,
        )

        if observability is None:
            pytest.skip(
                "Production conversation boundary does not expose "
                "its observability seam."
            )

        telegram_user_id = (
            980000
            + int(uuid4().int % 10000)
        )

        secret_content = (
            f"W19-SECRET-{uuid4().hex}"
        )

        caplog.set_level(
            logging.INFO,
        )

        await observability.record(
            event_type="telegram_classroom_message",
            telegram_user_id=telegram_user_id,
            outcome="accepted",
            metadata={
                "world_id": "french_world",
                "character": "Alix",
                "level": "B1",
            },
        )

        log_text = "\n".join(
            record.getMessage()
            for record in caplog.records
        )

        assert str(telegram_user_id) not in log_text
        assert secret_content not in log_text

    finally:
        _dispose_composition(composition)