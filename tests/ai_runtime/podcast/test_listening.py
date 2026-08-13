"""
Tests for provider-independent Podcast Listening Proposals.
"""

import pytest

from src.ai_runtime.podcast.listening import (
    ListeningProposal,
    ListeningProposalAction,
)


def make_proposal() -> ListeningProposal:
    return ListeningProposal(
        user_id="user-001",
        podcast_id="podcast-001",
        podcast_title="L'IA en Europe",
        podcast_url=(
            "https://example.com/podcast/ia-en-europe"
        ),
        character_id="yeti",
        character_name="Yeti",
        message=(
            "Would you like to listen to this podcast?"
        ),
        action=ListeningProposalAction.LISTEN,
        reason=(
            "It matches your French learning interests."
        ),
        target_language="fr",
        learner_level="B2",
    )


def test_listening_proposal_can_be_created():
    proposal = make_proposal()

    assert proposal.user_id == "user-001"

    assert proposal.podcast_id == (
        "podcast-001"
    )

    assert proposal.podcast_title == (
        "L'IA en Europe"
    )

    assert proposal.podcast_url == (
        "https://example.com/podcast/ia-en-europe"
    )

    assert proposal.character_id == "yeti"

    assert proposal.character_name == "Yeti"

    assert proposal.action == (
        ListeningProposalAction.LISTEN
    )

    assert proposal.target_language == "fr"

    assert proposal.learner_level == "B2"


def test_listening_proposal_is_passive():
    proposal = make_proposal()

    assert proposal.is_passive is True


def test_listening_proposal_supports_open_action():
    proposal = ListeningProposal(
        user_id="user-001",
        podcast_id="podcast-001",
        podcast_title="L'IA en Europe",
        podcast_url=(
            "https://example.com/podcast/ia-en-europe"
        ),
        character_id="yeti",
        character_name="Yeti",
        message=(
            "You can open this podcast if you want."
        ),
        action=ListeningProposalAction.OPEN,
        reason=(
            "The podcast is relevant to your learning."
        ),
        target_language="fr",
        learner_level="B2",
    )

    assert proposal.action == (
        ListeningProposalAction.OPEN
    )

    assert proposal.is_passive is True


@pytest.mark.parametrize(
    "field_name",
    [
        "user_id",
        "podcast_id",
        "podcast_title",
        "podcast_url",
        "character_id",
        "character_name",
        "message",
        "reason",
        "target_language",
        "learner_level",
    ],
)
def test_empty_required_fields_are_rejected(
    field_name: str,
):
    values = {
        "user_id": "user-001",
        "podcast_id": "podcast-001",
        "podcast_title": "L'IA en Europe",
        "podcast_url": (
            "https://example.com/podcast/ia-en-europe"
        ),
        "character_id": "yeti",
        "character_name": "Yeti",
        "message": (
            "Would you like to listen to this podcast?"
        ),
        "action": ListeningProposalAction.LISTEN,
        "reason": (
            "It matches your learning interests."
        ),
        "target_language": "fr",
        "learner_level": "B2",
    }

    values[field_name] = ""

    with pytest.raises(
        ValueError,
        match=f"ListeningProposal {field_name}",
    ):
        ListeningProposal(**values)


def test_invalid_podcast_url_is_rejected():
    values = {
        "user_id": "user-001",
        "podcast_id": "podcast-001",
        "podcast_title": "L'IA en Europe",
        "podcast_url": "javascript:play()",
        "character_id": "yeti",
        "character_name": "Yeti",
        "message": (
            "Would you like to listen to this podcast?"
        ),
        "action": ListeningProposalAction.LISTEN,
        "reason": (
            "It matches your learning interests."
        ),
        "target_language": "fr",
        "learner_level": "B2",
    }

    with pytest.raises(
        ValueError,
        match="podcast_url must use HTTP or HTTPS",
    ):
        ListeningProposal(**values)


def test_listening_proposal_is_immutable():
    proposal = make_proposal()

    with pytest.raises(
        AttributeError,
    ):
        proposal.podcast_title = "Changed"


def test_listening_proposal_does_not_contain_provider_credentials():
    proposal = make_proposal()

    fields = proposal.__dataclass_fields__

    assert "api_key" not in fields

    assert "access_token" not in fields

    assert "client_secret" not in fields

    assert "provider_token" not in fields