import pytest

from backend.conversation.conversation_request import (
    ConversationRequest,
)


def test_conversation_request_is_created():

    request = ConversationRequest(
        system_instruction=(
            "You are a friendly learning companion."
        ),
        user_prompt=(
            "Explain artificial intelligence."
        ),
        character_id="yeti",
        character_name="Yeti",
    )

    assert request.character_id == "yeti"

    assert request.character_name == "Yeti"

    assert request.user_prompt == (
        "Explain artificial intelligence."
    )

    assert (
        request.has_conversation_context
        is False
    )

    assert request.context_length == 0


def test_conversation_request_accepts_intelligence_context():

    request = ConversationRequest(
        system_instruction=(
            "You are a friendly learning companion."
        ),
        user_prompt=(
            "Explain the latest AI regulation."
        ),
        conversation_context=(
            "LIVE INTELLIGENCE\n"
            "Research query: Latest AI regulation"
        ),
        character_id="yeti",
        character_name="Yeti",
    )

    assert (
        request.has_conversation_context
        is True
    )

    assert request.context_length > 0

    assert (
        "LIVE INTELLIGENCE"
        in request.conversation_context
    )


def test_conversation_request_rejects_empty_instruction():

    with pytest.raises(
        ValueError,
        match="system_instruction cannot be empty",
    ):
        ConversationRequest(
            system_instruction=" ",
            user_prompt="Explain AI",
        )


def test_conversation_request_rejects_empty_prompt():

    with pytest.raises(
        ValueError,
        match="user_prompt cannot be empty",
    ):
        ConversationRequest(
            system_instruction="You are helpful.",
            user_prompt=" ",
        )


def test_conversation_request_rejects_blank_context():

    with pytest.raises(
        ValueError,
        match="conversation_context cannot be blank",
    ):
        ConversationRequest(
            system_instruction="You are helpful.",
            user_prompt="Explain AI",
            conversation_context=" ",
        )


def test_conversation_request_summary_is_safe():

    request = ConversationRequest(
        system_instruction="You are helpful.",
        user_prompt="Explain AI.",
        conversation_context="Private context.",
        character_id="yeti",
        character_name="Yeti",
    )

    summary = request.summary()

    assert summary["character_id"] == "yeti"

    assert summary["character_name"] == "Yeti"

    assert summary["has_context"] == "True"

    assert "Private context." not in summary

    assert "Explain AI." not in summary