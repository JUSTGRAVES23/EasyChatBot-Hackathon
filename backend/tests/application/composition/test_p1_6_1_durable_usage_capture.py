"""P1.6.1 regression: production composition attaches durable usage capture."""

import asyncio

from app.application.composition.beta_telegram_composition import (
    create_beta_telegram_composition,
)
from app.application.providers.provider_usage_capture import (
    ProviderUsageCapture,
)
from app.ai_runtime.conversation.conversation_runtime import ConversationRuntime
from tests.application.composition.deterministic_language_detector import (
    DeterministicLanguageDetector,
)


def test_factory_runtime_gets_durable_usage_capture():
    class FakeRepository:
        def __init__(self):
            self.event = None

        def save(self, event):
            self.event = event

        def get_all(self):
            return [] if self.event is None else [self.event]

        def clear(self):
            self.event = None

    class FakeProvider:
        async def generate(self, *, system_prompt, user_message):
            from app.providers.provider_result import (
                ProviderResult,
                ProviderUsage,
            )

            return ProviderResult(
                success=True,
                provider_id="p1_6_1_fake",
                model="deterministic",
                content="ok",
                usage=ProviderUsage(
                    input_tokens=2,
                    output_tokens=3,
                    total_tokens=5,
                ),
                provider_request_id="req-p1-6-1",
                latency_ms=7,
            )

    class FakeUserRepository:
        pass

    class FakeTokenRepository:
        pass

    class FakeBindingRepository:
        pass

    class FakeConversationEventRepository:
        pass

    class FakePrivacyIdentifierService:
        pass

    class FakeConversationEventValidator:
        pass

    repo = FakeRepository()

    runtime = ConversationRuntime(
        llm_provider=FakeProvider(),
    )

    composition = create_beta_telegram_composition(
        user_repository=FakeUserRepository(),
        token_repository=FakeTokenRepository(),
        binding_repository=FakeBindingRepository(),
        conversation_event_repository=FakeConversationEventRepository(),
        privacy_identifier_service=FakePrivacyIdentifierService(),
        conversation_event_validator=FakeConversationEventValidator(),
        conversation_runtime_factory=lambda: runtime,
        provider_usage_repository=repo,
        language_detector=DeterministicLanguageDetector(),
    )

    resolved = composition.conversation_runtime

    assert isinstance(resolved, ConversationRuntime)
    assert isinstance(resolved.usage_capture, ProviderUsageCapture)

    result = asyncio.run(
        resolved.respond(
            character_instruction="You are a test tutor.",
            learner_message="Bonjour",
        )
    )

    assert result == "ok"
    assert repo.event is not None
    assert repo.event.provider == "p1_6_1_fake"
    assert repo.event.model == "deterministic"
    assert repo.event.input_tokens == 2
    assert repo.event.output_tokens == 3
    assert repo.event.latency_ms == 7
    assert repo.event.success is True


def test_factory_runtime_captures_failure_before_runtime_raises():
    class FakeRepository:
        def __init__(self):
            self.event = None

        def save(self, event):
            self.event = event

        def get_all(self):
            return [] if self.event is None else [self.event]

        def clear(self):
            self.event = None

    class FailingProvider:
        async def generate(self, *, system_prompt, user_message):
            from app.providers.provider_result import (
                ProviderResult,
            )

            return ProviderResult(
                success=False,
                provider_id="p1_6_1_failure",
                model="deterministic",
                content=None,
                error="deterministic provider failure",
                latency_ms=9,
            )

    class FakeUserRepository:
        pass

    class FakeTokenRepository:
        pass

    class FakeBindingRepository:
        pass

    class FakeConversationEventRepository:
        pass

    class FakePrivacyIdentifierService:
        pass

    class FakeConversationEventValidator:
        pass

    repo = FakeRepository()

    runtime = ConversationRuntime(
        llm_provider=FailingProvider(),
    )

    composition = create_beta_telegram_composition(
        user_repository=FakeUserRepository(),
        token_repository=FakeTokenRepository(),
        binding_repository=FakeBindingRepository(),
        conversation_event_repository=FakeConversationEventRepository(),
        privacy_identifier_service=FakePrivacyIdentifierService(),
        conversation_event_validator=FakeConversationEventValidator(),
        conversation_runtime_factory=lambda: runtime,
        provider_usage_repository=repo,
        language_detector=DeterministicLanguageDetector(),
    )

    resolved = composition.conversation_runtime

    assert isinstance(resolved, ConversationRuntime)
    assert isinstance(resolved.usage_capture, ProviderUsageCapture)

    try:
        asyncio.run(
            resolved.respond(
                character_instruction="You are a test tutor.",
                learner_message="Bonjour",
            )
        )
    except RuntimeError as exc:
        assert "deterministic provider failure" in str(exc)
    else:
        raise AssertionError("Expected ConversationRuntime to raise RuntimeError")

    assert repo.event is not None
    assert repo.event.provider == "p1_6_1_failure"
    assert repo.event.success is False

