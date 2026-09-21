from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field
from app.api.dependencies.authorization import require_permission
from app.domain.authorization.permissions import Permission
from ..application.project_discovery_service import DiscoveryCandidateConflictError, DiscoveryCandidateNotFoundError, DiscoveryCandidateStateError, ProjectDiscoveryService

class ProjectDiscoveryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_key: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    owner: str | None = Field(default=None, max_length=255)
    source: str = Field(min_length=1, max_length=255)
    source_reference: str | None = Field(default=None, max_length=1000)

def create_project_discovery_router(project_discovery: ProjectDiscoveryService) -> APIRouter:
    if project_discovery is None: raise ValueError("project_discovery cannot be None.")
    router = APIRouter(prefix="/project-control/discovery", tags=["Project Discovery"])
    permission = require_permission(Permission.FUNCTIONALITY_CONTROL)

    @router.get("/candidates", dependencies=[Depends(permission)])
    async def list_candidates():
        return jsonable_encoder(project_discovery.list_candidates())

    @router.post("/candidates", status_code=201, dependencies=[Depends(permission)])
    async def create_candidate(request: ProjectDiscoveryCreateRequest):
        try: return jsonable_encoder(project_discovery.create_candidate(**request.model_dump()))
        except DiscoveryCandidateConflictError as exc: raise HTTPException(409, str(exc)) from exc
        except ValueError as exc: raise HTTPException(422, str(exc)) from exc

    @router.get("/candidates/{candidate_id}", dependencies=[Depends(permission)])
    async def get_candidate(candidate_id: str):
        try: return jsonable_encoder(project_discovery.get_candidate(candidate_id))
        except DiscoveryCandidateNotFoundError as exc: raise HTTPException(404, str(exc)) from exc

    @router.post("/candidates/{candidate_id}/review", dependencies=[Depends(permission)])
    async def review_candidate(candidate_id: str):
        try: return jsonable_encoder(project_discovery.review_candidate(candidate_id))
        except DiscoveryCandidateNotFoundError as exc: raise HTTPException(404, str(exc)) from exc
        except DiscoveryCandidateStateError as exc: raise HTTPException(409, str(exc)) from exc

    @router.post("/candidates/{candidate_id}/accept", dependencies=[Depends(permission)])
    async def accept_candidate(candidate_id: str):
        try: return jsonable_encoder(project_discovery.accept_candidate(candidate_id))
        except DiscoveryCandidateNotFoundError as exc: raise HTTPException(404, str(exc)) from exc
        except (DiscoveryCandidateConflictError, DiscoveryCandidateStateError) as exc: raise HTTPException(409, str(exc)) from exc

    @router.post("/candidates/{candidate_id}/reject", dependencies=[Depends(permission)])
    async def reject_candidate(candidate_id: str):
        try: return jsonable_encoder(project_discovery.reject_candidate(candidate_id))
        except DiscoveryCandidateNotFoundError as exc: raise HTTPException(404, str(exc)) from exc
        except DiscoveryCandidateStateError as exc: raise HTTPException(409, str(exc)) from exc

    return router
