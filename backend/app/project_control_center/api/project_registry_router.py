from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies.authorization import require_permission
from app.domain.authorization.permissions import Permission

from ..application.project_registry_excel_service import (
    ProjectRegistryExcelError,
    ProjectRegistryExcelService,
)
from ..application.project_registry_service import (
    ProjectAlreadyExistsError,
    ProjectRegistryPersistenceError,
    ProjectRegistryService,
)


class ProjectRegistryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    owner: str | None = Field(default=None, max_length=255)
    active: bool = True


class ProjectRegistryPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    owner: str | None = Field(default=None, max_length=255)
    active: bool | None = None


def create_project_registry_router(
    project_registry: ProjectRegistryService,
    *,
    bulk_writer=None,
) -> APIRouter:
    """Create the authorized authoritative Project Registry API."""
    if project_registry is None:
        raise ValueError("project_registry cannot be None.")
    excel_service = (
        ProjectRegistryExcelService(project_registry, bulk_writer)
        if bulk_writer is not None
        else None
    )

    router = APIRouter(
        prefix="/project-control/registry",
        tags=["Project Registry"],
    )

    permission_dependency = require_permission(Permission.FUNCTIONALITY_CONTROL)

    @router.get(
        "/projects",
        summary="List active projects",
        dependencies=[Depends(permission_dependency)],
    )
    async def list_projects() -> list[dict[str, object]]:
        return jsonable_encoder(project_registry.list_projects())

    @router.post(
        "/projects",
        status_code=status.HTTP_201_CREATED,
        summary="Create project",
        dependencies=[Depends(permission_dependency)],
    )
    async def create_project(
        request: ProjectRegistryCreateRequest,
    ) -> dict[str, object]:
        try:
            project = project_registry.create_project(
                project_id=request.project_id,
                name=request.name,
                description=request.description,
                owner=request.owner,
                active=request.active,
            )
        except ProjectAlreadyExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ProjectRegistryPersistenceError as exc:
            raise HTTPException(
                status_code=500,
                detail="Project persistence failed.",
            ) from exc
        return jsonable_encoder(project)

    if excel_service is not None:
        @router.get(
            "/projects/export",
            summary="Export active Project Registry as XLSX",
            dependencies=[Depends(permission_dependency)],
        )
        async def export_projects() -> StreamingResponse:
            content = excel_service.export_projects()
            return StreamingResponse(
                BytesIO(content),
                media_type=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
                headers={
                    "Content-Disposition": 'attachment; filename="Project_Control_Registry.xlsx"',
                    "Cache-Control": "no-store",
                },
            )

        @router.post(
            "/projects/import",
            summary="Import Project Registry from XLSX",
            status_code=status.HTTP_200_OK,
            dependencies=[Depends(permission_dependency)],
        )
        async def import_projects(
            file: UploadFile = File(...),
            mode: str = Query(default="create_only", pattern="^(create_only|upsert)$"),
        ) -> dict[str, object]:
            filename = (file.filename or "").lower()
            if not filename.endswith(".xlsx"):
                raise HTTPException(
                    status_code=422,
                    detail="Only .xlsx workbooks are supported.",
                )

            content = await file.read(5 * 1024 * 1024 + 1)
            try:
                result = excel_service.import_projects(content, mode=mode)
            except ProjectRegistryExcelError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            except (ValueError, RuntimeError) as exc:
                raise HTTPException(
                    status_code=500,
                    detail="Project Registry import failed.",
                ) from exc
            finally:
                await file.close()

            return {
                "imported": result.imported,
                "mode": result.mode,
                "projects": jsonable_encoder(result.projects),
            }


    @router.get(
        "/projects/{project_id}",
        summary="Get registered project",
        dependencies=[Depends(permission_dependency)],
    )
    async def get_project(project_id: str) -> dict[str, object]:
        try:
            project = project_registry.get_project(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if project is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown project: {project_id}",
            )
        return jsonable_encoder(project)

    @router.patch(
        "/projects/{project_id}",
        summary="Update registered project",
        dependencies=[Depends(permission_dependency)],
    )
    async def update_project(
        project_id: str,
        request: ProjectRegistryPatchRequest,
    ) -> dict[str, object]:
        if (
            request.name is None
            and request.description is None
            and request.owner is None
            and request.active is None
        ):
            raise HTTPException(
                status_code=422,
                detail="At least one project field is required.",
            )
        try:
            project = project_registry.update_project(
                project_id,
                name=request.name,
                description=request.description,
                owner=request.owner,
                active=request.active,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ProjectRegistryPersistenceError as exc:
            raise HTTPException(
                status_code=500,
                detail="Project persistence failed.",
            ) from exc
        if project is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown project: {project_id}",
            )
        return jsonable_encoder(project)

    return router


__all__ = [
    "ProjectRegistryCreateRequest",
    "ProjectRegistryPatchRequest",
    "create_project_registry_router",
]
