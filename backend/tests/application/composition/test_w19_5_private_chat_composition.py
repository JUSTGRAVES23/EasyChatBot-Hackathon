from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.application.composition import beta_telegram_composition as composition


class FakePrivateChatBridge:
    def __init__(self, *, private_chat_service_factory):
        self.private_chat_service_factory = private_chat_service_factory


class FakeConversationBoundary:
    last_kwargs = None

    def __init__(self, **kwargs):
        type(self).last_kwargs = kwargs


class FakeConversationService:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakeBetaAccessService:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakePrivateChatGate:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakeStartHandler:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakeAdapter:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakeRuntime:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


@pytest.mark.parametrize("factory_value", [lambda: object()])
def test_create_beta_telegram_composition_wires_private_chat_bridge(
    monkeypatch: pytest.MonkeyPatch,
    factory_value,
) -> None:
    monkeypatch.setattr(
        composition,
        "BetaAccessService",
        FakeBetaAccessService,
    )
    monkeypatch.setattr(
        composition,
        "TelegramConversationService",
        FakeConversationService,
    )
    monkeypatch.setattr(
        composition,
        "TelegramPrivateChatBridge",
        FakePrivateChatBridge,
    )
    monkeypatch.setattr(
        composition,
        "BetaTelegramConversationBoundary",
        FakeConversationBoundary,
    )
    monkeypatch.setattr(
        composition,
        "BetaPrivateChatGate",
        FakePrivateChatGate,
    )
    monkeypatch.setattr(
        composition,
        "BetaTelegramStartHandler",
        FakeStartHandler,
    )
    monkeypatch.setattr(
        composition,
        "BetaTelegramAdapter",
        FakeAdapter,
    )
    monkeypatch.setattr(
        composition,
        "TelegramBotRuntime",
        FakeRuntime,
    )

    runtime = object()
    beta_world_access_service = object()
    language_detector = object()
    world_resolver = object()
    language_policy = object()

    result = composition.create_beta_telegram_composition(
        user_repository=object(),
        token_repository=object(),
        binding_repository=object(),
        conversation_event_repository=object(),
        privacy_identifier_service=object(),
        conversation_event_validator=object(),
        beta_world_access_service=beta_world_access_service,
        conversation_runtime=runtime,
        world_resolver=world_resolver,
        language_response_policy=language_policy,
        language_detector=language_detector,
        private_chat_service_factory=factory_value,
    )

    bridge = result.private_chat_bridge

    assert bridge is not None
    assert bridge.private_chat_service_factory is factory_value

    boundary_kwargs = FakeConversationBoundary.last_kwargs
    assert boundary_kwargs is not None
    assert boundary_kwargs["private_chat_bridge"] is bridge

    assert result.conversation_boundary is not None
    assert result.private_chat_bridge is bridge
