from dataclasses import dataclass


import pytest


LIFECYCLES = {
    "planning",
    "development",
    "maintenance",
    "completed",
    "archived",
}

STATUSES = {
    "on_track",
    "at_risk",
    "blocked",
    "complete",
    "paused",
}


@dataclass(frozen=True)
class Project:
    project_id: str
    project_name: str
    lifecycle: str
    status: str
    progress_percent: float

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise ValueError("project_id is required")

        if not self.project_name.strip():
            raise ValueError("project_name is required")

        if self.lifecycle not in LIFECYCLES:
            raise ValueError("invalid lifecycle")

        if self.status not in STATUSES:
            raise ValueError("invalid status")

        if not 0 <= self.progress_percent <= 100:
            raise ValueError("progress_percent must be between 0 and 100")


def test_easychatbot_project_contract() -> None:
    project = Project(
        "easychatbot",
        "EasyChatBot",
        "development",
        "on_track",
        85,
    )

    assert project.project_id == "easychatbot"
    assert project.status == "on_track"
    assert project.progress_percent == 85


@pytest.mark.parametrize("progress", [-1, 100.1])
def test_progress_is_bounded(progress: float) -> None:
    with pytest.raises(ValueError):
        Project(
            "x",
            "X",
            "planning",
            "on_track",
            progress,
        )


def test_lifecycle_and_status_are_distinct() -> None:
    project = Project(
        "x",
        "X",
        "development",
        "at_risk",
        50,
    )

    assert project.lifecycle == "development"
    assert project.status == "at_risk"