"""
Tests for LiveKit Agent Dispatcher.

Validates the infrastructure boundary between
EasyChatBot voice-call metadata and LiveKit Agent
dispatch.

These tests do not contact LiveKit Cloud.
"""

from __future__ import annotations


from types import SimpleNamespace
from unittest.mock import MagicMock, patch


import pytest


from app.infrastructure.voice.livekit_agent_dispatcher import (
    LiveKitAgentDispatcher,
)


def create_dispatcher() -> LiveKitAgentDispatcher:
    """
    Create a configured dispatcher for tests.
    """

    return LiveKitAgentDispatcher(
        agent_name="easychatbot-voice",
    )


@patch(
    "app.infrastructure.voice.livekit_agent_dispatcher.api.LiveKitAPI"
)
def test_dispatch_creates_livekit_agent_dispatch(
    mock_livekit_api,
):
    """
    Dispatcher creates a LiveKit Agent dispatch.
    """

    mock_dispatch = SimpleNamespace(
        id="dispatch-001",
    )

    mock_api = MagicMock()

    mock_api.agent_dispatch.create_dispatch.return_value = (
        mock_dispatch
    )

    mock_livekit_api.return_value = mock_api

    with patch.dict(
        "os.environ",
        {
            "LIVEKIT_URL": (
                "wss://test.livekit.cloud"
            ),
            "LIVEKIT_API_KEY": "test-api-key",
            "LIVEKIT_API_SECRET": "test-api-secret",
        },
        clear=False,
    ):

        dispatcher = create_dispatcher()

        dispatch_id = dispatcher.dispatch(
            room_name="yeti-room-001",
            learner_id="learner-001",
            world_id="french_world",
            character_id="yeti",
            language_code="fr",
        )


    assert dispatch_id == (
        "dispatch-001"
    )


    mock_livekit_api.assert_called_once_with(
        url="wss://test.livekit.cloud",
        api_key="test-api-key",
        api_secret="test-api-secret",
    )


    mock_api.agent_dispatch.create_dispatch.assert_called_once()


    mock_api.aclose.assert_called_once()


@patch(
    "app.infrastructure.voice.livekit_agent_dispatcher.api.LiveKitAPI"
)
def test_dispatch_passes_expected_metadata(
    mock_livekit_api,
):
    """
    Dispatcher passes the approved voice-call
    metadata to the LiveKit worker.
    """

    mock_dispatch = SimpleNamespace(
        id="dispatch-002",
    )

    mock_api = MagicMock()

    mock_api.agent_dispatch.create_dispatch.return_value = (
        mock_dispatch
    )

    mock_livekit_api.return_value = mock_api

    with patch.dict(
        "os.environ",
        {
            "LIVEKIT_URL": (
                "wss://test.livekit.cloud"
            ),
            "LIVEKIT_API_KEY": "test-api-key",
            "LIVEKIT_API_SECRET": "test-api-secret",
        },
        clear=False,
    ):

        dispatcher = create_dispatcher()

        dispatcher.dispatch(
            room_name="yeti-room-002",
            learner_id="learner-002",
            world_id="french_world",
            character_id="yeti",
            language_code="fr",
        )


    request = (
        mock_api
        .agent_dispatch
        .create_dispatch
        .call_args.args[0]
    )


    assert request.agent_name == (
        "easychatbot-voice"
    )


    assert request.room == (
        "yeti-room-002"
    )


    assert request.metadata == (
        '{"learner_id":"learner-002",'
        '"world_id":"french_world",'
        '"character_id":"yeti",'
        '"language_code":"fr"}'
    )


@patch(
    "app.infrastructure.voice.livekit_agent_dispatcher.api.LiveKitAPI"
)
def test_dispatch_uses_configured_agent_name(
    mock_livekit_api,
):
    """
    Dispatcher uses its configured agent name.
    """

    mock_dispatch = SimpleNamespace(
        id="dispatch-003",
    )

    mock_api = MagicMock()

    mock_api.agent_dispatch.create_dispatch.return_value = (
        mock_dispatch
    )

    mock_livekit_api.return_value = mock_api

    with patch.dict(
        "os.environ",
        {
            "LIVEKIT_URL": (
                "wss://test.livekit.cloud"
            ),
            "LIVEKIT_API_KEY": "test-api-key",
            "LIVEKIT_API_SECRET": "test-api-secret",
        },
        clear=False,
    ):

        dispatcher = LiveKitAgentDispatcher(
            agent_name="custom-voice-agent",
        )

        dispatcher.dispatch(
            room_name="room-003",
            learner_id="learner-003",
            world_id="french_world",
            character_id="yeti",
            language_code="fr",
        )


    request = (
        mock_api
        .agent_dispatch
        .create_dispatch
        .call_args.args[0]
    )


    assert request.agent_name == (
        "custom-voice-agent"
    )


@patch(
    "app.infrastructure.voice.livekit_agent_dispatcher.api.LiveKitAPI"
)
def test_dispatch_rejects_empty_room_name(
    mock_livekit_api,
):
    """
    Empty room names are rejected before
    contacting LiveKit.
    """

    dispatcher = create_dispatcher()

    with pytest.raises(
        ValueError,
        match="room_name cannot be empty",
    ):

        dispatcher.dispatch(
            room_name="",
            learner_id="learner-001",
            world_id="french_world",
            character_id="yeti",
            language_code="fr",
        )


    mock_livekit_api.assert_not_called()


@patch(
    "app.infrastructure.voice.livekit_agent_dispatcher.api.LiveKitAPI"
)
def test_dispatch_rejects_empty_character_id(
    mock_livekit_api,
):
    """
    Empty character identifiers are rejected.
    """

    dispatcher = create_dispatcher()

    with pytest.raises(
        ValueError,
        match="character_id cannot be empty",
    ):

        dispatcher.dispatch(
            room_name="room-001",
            learner_id="learner-001",
            world_id="french_world",
            character_id="",
            language_code="fr",
        )


    mock_livekit_api.assert_not_called()


def test_dispatch_requires_livekit_api_key():
    """
    Missing LiveKit API key is rejected.

    The environment is cleared so the test cannot
    accidentally inherit LIVEKIT_API_KEY from the
    developer's local .env file.
    """

    dispatcher = create_dispatcher()

    with patch.dict(
        "os.environ",
        {
            "LIVEKIT_URL": (
                "wss://test.livekit.cloud"
            ),
            "LIVEKIT_API_SECRET": (
                "test-api-secret"
            ),
        },
        clear=True,
    ):

        with patch(
            "app.infrastructure.voice.livekit_agent_dispatcher.api.LiveKitAPI"
        ) as mock_livekit_api:

            with pytest.raises(
                ValueError,
                match="LIVEKIT_API_KEY is not configured",
            ):

                dispatcher.dispatch(
                    room_name="room-001",
                    learner_id="learner-001",
                    world_id="french_world",
                    character_id="yeti",
                    language_code="fr",
                )


            mock_livekit_api.assert_not_called()


def test_dispatch_requires_livekit_api_secret():
    """
    Missing LiveKit API secret is rejected.

    The environment is cleared so the test cannot
    accidentally inherit LIVEKIT_API_SECRET from the
    developer's local .env file.
    """

    dispatcher = create_dispatcher()

    with patch.dict(
        "os.environ",
        {
            "LIVEKIT_URL": (
                "wss://test.livekit.cloud"
            ),
            "LIVEKIT_API_KEY": (
                "test-api-key"
            ),
        },
        clear=True,
    ):

        with patch(
            "app.infrastructure.voice.livekit_agent_dispatcher.api.LiveKitAPI"
        ) as mock_livekit_api:

            with pytest.raises(
                ValueError,
                match="LIVEKIT_API_SECRET is not configured",
            ):

                dispatcher.dispatch(
                    room_name="room-001",
                    learner_id="learner-001",
                    world_id="french_world",
                    character_id="yeti",
                    language_code="fr",
                )


            mock_livekit_api.assert_not_called()


def test_dispatch_requires_livekit_url():
    """
    Missing LiveKit URL is rejected.

    The environment is cleared so the test cannot
    accidentally inherit LIVEKIT_URL from the
    developer's local .env file.
    """

    dispatcher = create_dispatcher()

    with patch.dict(
        "os.environ",
        {
            "LIVEKIT_API_KEY": (
                "test-api-key"
            ),
            "LIVEKIT_API_SECRET": (
                "test-api-secret"
            ),
        },
        clear=True,
    ):

        with patch(
            "app.infrastructure.voice.livekit_agent_dispatcher.api.LiveKitAPI"
        ) as mock_livekit_api:

            with pytest.raises(
                ValueError,
                match="LIVEKIT_URL is not configured",
            ):

                dispatcher.dispatch(
                    room_name="room-001",
                    learner_id="learner-001",
                    world_id="french_world",
                    character_id="yeti",
                    language_code="fr",
                )


            mock_livekit_api.assert_not_called()