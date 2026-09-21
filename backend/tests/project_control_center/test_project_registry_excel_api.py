from __future__ import annotations

from io import BytesIO

from fastapi import FastAPI
from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.api.dependencies.authorization import get_current_principal
from app.domain.identity.principal import Principal
from app.project_control_center.api.project_registry_router import create_project_registry_router
from app.project_control_center.domain.models import ProjectDefinition


class FakeRegistryService:
    def __init__(self) -> None:
        self.projects = {
            "easychatbot": ProjectDefinition(project_id="easychatbot", name="EasyChatBot")
        }

    def list_projects(self) -> list[ProjectDefinition]:
        return list(self.projects.values())

    def get_project(self, project_id: str) -> ProjectDefinition | None:
        return self.projects.get(project_id)

    def create_project(self, *, project_id, name, description="", owner=None, active=True):
        if project_id in self.projects:
            raise ValueError(f"Project already exists: {project_id}")
        project = ProjectDefinition(project_id=project_id, name=name, description=description, owner=owner, active=active)
        self.projects[project_id] = project
        return project

    def update_project(self, project_id, *, name=None, description=None, owner=None, active=None):
        current = self.projects.get(project_id)
        if current is None:
            return None
        project = ProjectDefinition(
            project_id=current.project_id,
            name=current.name if name is None else name,
            description=current.description if description is None else description,
            owner=current.owner if owner is None else owner,
            active=current.active if active is None else active,
            created_at=current.created_at,
        )
        self.projects[project_id] = project
        return project


class FakeBulkWriter:
    def __init__(self, service: FakeRegistryService) -> None:
        self.service = service

    def create_many(self, projects):
        for project in projects:
            if project.project_id in self.service.projects:
                raise ValueError(f"Project already exists: {project.project_id}")
        for project in projects:
            self.service.projects[project.project_id] = project
        return projects

    def upsert_many(self, projects):
        for project in projects:
            self.service.projects[project.project_id] = project
        return projects


def _principal(roles: tuple[str, ...]) -> Principal:
    return Principal(
        user_id="operator-001",
        email="operator@example.com",
        email_verified=True,
        account_status="active",
        roles=roles,
    )


def _xlsx() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Projects"
    sheet.append(["project_id", "name", "description", "owner", "active", "created_at"])
    sheet.append(["imported", "Imported", "", "", True, ""])
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def _client(roles: tuple[str, ...] = ("developer_admin",)) -> TestClient:
    application = FastAPI()
    service = FakeRegistryService()
    application.include_router(
        create_project_registry_router(
            service,
            bulk_writer=FakeBulkWriter(service),
        )
    )

    async def override_current_principal() -> Principal:
        return _principal(roles)

    application.dependency_overrides[get_current_principal] = override_current_principal
    return TestClient(application)


def test_export_endpoint_returns_xlsx() -> None:
    with _client() as client:
        response = client.get("/project-control/registry/projects/export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.content.startswith(b"PK")
    assert "Project_Control_Registry.xlsx" in response.headers["content-disposition"]


def test_import_endpoint_accepts_xlsx() -> None:
    with _client() as client:
        response = client.post(
            "/project-control/registry/projects/import",
            files={"file": ("registry.xlsx", _xlsx(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert response.status_code == 200
    assert response.json()["imported"] == 1


def test_import_endpoint_rejects_non_xlsx() -> None:
    with _client() as client:
        response = client.post(
            "/project-control/registry/projects/import",
            files={"file": ("registry.txt", b"not xlsx", "text/plain")},
        )

    assert response.status_code == 422


def test_beta_user_is_denied() -> None:
    with _client(("beta_user",)) as client:
        response = client.get("/project-control/registry/projects/export")

    assert response.status_code == 403
