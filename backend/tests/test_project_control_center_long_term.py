from app.project_control_center.application.history_service import ProjectHistoryService
from app.project_control_center.application.service import ProjectControlService
from app.project_control_center.domain.models import ProjectDefinition, ProjectEventType
from app.project_control_center.infrastructure.demo_source import DemoProjectStatusSource
from app.project_control_center.infrastructure.in_memory import (
    InMemoryProjectEventRepository,
    InMemoryProjectRegistry,
    InMemorySnapshotRepository,
)
from app.project_control_center.integration.project_manager_agent import (
    ProjectManagerAgentContextBuilder,
)


def make_services():
    registry = InMemoryProjectRegistry()
    snapshots = InMemorySnapshotRepository()
    registry.save(ProjectDefinition("easychatbot", "EasyChatBot"))
    control = ProjectControlService(
        registry=registry,
        sources=(DemoProjectStatusSource(),),
        snapshots=snapshots,
    )
    return registry, snapshots, control


def test_phase_1_builds_project_snapshot():
    _, snapshots, control = make_services()
    snapshot = control.get_snapshot("easychatbot")
    assert snapshot.project_id == "easychatbot"
    assert snapshot.project_name == "EasyChatBot"
    assert snapshot.overall_progress_percent == 81.3
    assert snapshot.open_risks == 2
    assert snapshots.list_for_project("easychatbot")


def test_new_project_is_data_not_code():
    registry, _, control = make_services()
    registry.save(ProjectDefinition("risk-intelligence", "Risk Intelligence"))
    snapshot = control.get_snapshot("risk-intelligence")
    assert snapshot.project_id == "risk-intelligence"
    assert snapshot.project_name == "Risk Intelligence"


def test_project_manager_context_is_read_only():
    _, _, control = make_services()
    snapshot = control.get_snapshot("easychatbot", persist=False)
    context = ProjectManagerAgentContextBuilder.build(snapshot)
    assert context["project"]["status"] in {"on_track", "at_risk", "blocked", "complete", "unknown"}
    assert context["rules"]
    assert "Do not invent missing project data." in context["rules"]


def test_history_service_reports_delta():
    _, snapshots, control = make_services()
    first = control.get_snapshot("easychatbot")
    second = control.get_snapshot("easychatbot")
    trend = ProjectHistoryService(snapshots).trend("easychatbot")
    assert len(trend.snapshots) == 2
    assert trend.progress_delta == 0


def test_event_repository_boundary():
    repository = InMemoryProjectEventRepository()
    from app.project_control_center.application.event_service import ProjectEventService
    event = ProjectEventService(repository).record(
        project_id="easychatbot",
        event_type=ProjectEventType.PROJECT_CREATED,
        summary="Project registered",
        source="project-control",
    )
    assert repository.list_for_project("easychatbot")[0] == event
