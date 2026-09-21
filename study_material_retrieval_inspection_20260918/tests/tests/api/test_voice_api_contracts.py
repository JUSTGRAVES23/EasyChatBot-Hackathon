"""
Voice API Contract Tests.

Validates stable frontend contracts.

Covers:
- Trigger response contract.
- Notification acceptance contract.
- Reconnect contract.

Does NOT:
- Test domain logic.
- Test repositories.
- Test providers.
"""

from fastapi.testclient import TestClient

from app.main import app


def test_voice_trigger_contract() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/voice/trigger",
            json={
                "learner_id": "learner-001",
                "character_id": "yeti",
                "world_id": "french_world",
                "language_code": "fr",
                "channel": "inbox",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert "voice_call_id" in body
    assert "invitation_id" in body
    assert "notification_id" in body


def test_voice_acceptance_contract() -> None:
    with TestClient(app) as client:
        trigger = client.post(
            "/voice/trigger",
            json={
                "learner_id": "learner-002",
                "character_id": "alix",
                "world_id": "french_world",
                "language_code": "fr",
                "channel": "inbox",
            },
        )

        assert trigger.status_code == 200

        notification_id = trigger.json()["notification_id"]

        response = client.post(
            f"/voice/notification/{notification_id}/accept"
        )

    assert response.status_code == 200

    body = response.json()

    assert "voice_call_id" in body
    assert "learner_id" in body
    assert "character_id" in body
    assert "session_id" in body
    assert "state" in body


def test_voice_reconnect_contract() -> None:
    with TestClient(app) as client:
        trigger = client.post(
            "/voice/trigger",
            json={
                "learner_id": "learner-003",
                "character_id": "yeti",
                "world_id": "french_world",
                "language_code": "fr",
                "channel": "inbox",
            },
        )

        assert trigger.status_code == 200

        voice_call_id = trigger.json()["voice_call_id"]

        response = client.post(
            f"/voice/call/{voice_call_id}/reconnect"
        )

    assert response.status_code == 200

    body = response.json()

    assert body["voice_call_id"] == voice_call_id
    assert "session_id" in body
    assert "state" in body


def test_unknown_voice_notification_contract() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/voice/notification/unknown/accept"
        )

    assert response.status_code == 404


def test_unknown_voice_call_reconnect_contract() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/voice/call/unknown/reconnect"
        )

    assert response.status_code == 404