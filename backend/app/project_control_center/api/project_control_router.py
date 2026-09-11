from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from app.api.dependencies.authorization import require_permission
from app.domain.authorization.permissions import Permission

from ..application.service import ProjectControlService


def create_project_control_router(
    project_control: ProjectControlService,
) -> APIRouter:
    """Create the read-only Project Control Center API router.

    Authorization is enforced at the HTTP boundary before the
    ProjectControlService is executed.

    The router:
    - requires FUNCTIONALITY_CONTROL permission;
    - exposes read-only project-control snapshots;
    - does not execute the Project Manager Agent;
    - does not call LLM/provider infrastructure;
    - does not mutate project state.
    """
    if project_control is None:
        raise ValueError(
            "project_control cannot be None."
        )

    router = APIRouter(
        prefix="/project-control",
        tags=["Project Control Center"],
    )

    permission_dependency = require_permission(
        Permission.FUNCTIONALITY_CONTROL,
    )

    @router.get(
        "/projects/{project_id}",
        summary="Get project control snapshot",
        description=(
            "Return the unified read-only Project Control "
            "Center snapshot for a project."
        ),
        dependencies=[
            Depends(permission_dependency),
        ],
    )
    async def get_project_control_snapshot(
        project_id: str,
    ) -> dict[str, object]:
        try:
            snapshot = (
                await project_control.get_snapshot_async(
                    project_id,
                    persist=False,
                )
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            ) from exc

        return jsonable_encoder(snapshot)

    return router


__all__ = [
    "create_project_control_router",
]
