from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api.questionnaires.api import QuestionnaireRuntime, create_app


def client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(QuestionnaireRuntime(tmp_path / "m4113.sqlite3"))
    )


def test_demo_questionnaire_is_api_backed(tmp_path: Path):
    api = client(tmp_path)

    response = api.get(
        "/api/academy/questionnaires/demo-questionnaire?mode=practice"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["questionnaire_id"] == "demo-questionnaire"
    assert len(payload["questions"]) == 3


def test_completion_returns_real_result_id_and_result_is_readable(
    tmp_path: Path,
):
    api = client(tmp_path)

    completion = api.post(
        "/api/academy/questionnaires/demo-questionnaire/complete",
        params={"user_id": "m4113-user", "mode": "practice"},
        json={
            "answers": [
                {"question_id": "demo-q1", "option_id": "a"},
                {"question_id": "demo-q2", "option_id": "a"},
                {"question_id": "demo-q3", "option_id": "a"},
            ]
        },
    )

    assert completion.status_code == 200

    result_id = completion.json()["result_id"]

    assert result_id
    assert result_id != "demo-result"

    result = api.get(
        f"/api/academy/questionnaire-results/{result_id}"
    )

    assert result.status_code == 200

    payload = result.json()

    assert payload["header"]["result_id"] == result_id
    assert payload["performance_summary"]["total_questions"] == 3
    assert payload["performance_summary"]["correct_answers"] == 3
    assert payload["performance_summary"]["score_percentage"] == 100.0


def test_unknown_result_is_not_available(tmp_path: Path):
    api = client(tmp_path)

    response = api.get(
        "/api/academy/questionnaire-results/demo-result"
    )

    assert response.status_code == 404
