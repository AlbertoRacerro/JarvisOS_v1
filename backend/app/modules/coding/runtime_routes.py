from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.core.config import get_settings
from app.modules.coding.pipeline_state import (
    DevelopmentPipelineStateService,
    PipelineStateInputError,
)
from app.modules.coding.repository_truth import RepositoryTruthService
from app.modules.coding.runtime_truth import (
    CANONICAL_RUNTIME_REPOSITORY,
    RuntimeSnapshot,
    RuntimeTruthService,
)

router = APIRouter(prefix="/api/coding", tags=["coding"])


@router.get("/runtime-truth")
def runtime_truth(
    request: Request,
    repository: str,
    target_ref: str,
) -> dict[str, object]:
    settings = get_settings()
    if repository != CANONICAL_RUNTIME_REPOSITORY or repository not in settings.coding_repositories:
        raise HTTPException(status_code=400, detail={"code": "repository_mismatch"})

    startup = getattr(request.app.state, "runtime_startup_snapshot", None)
    if not isinstance(startup, RuntimeSnapshot):
        raise HTTPException(status_code=503, detail={"code": "startup_snapshot_unavailable"})

    service = RuntimeTruthService(RepositoryTruthService(settings.coding_repositories))
    return service.inspect(repository=repository, target_ref=target_ref, startup=startup)


@router.get("/pipeline-state")
def pipeline_state(
    repository: str,
    pr_number: int,
    spec_id: str,
) -> dict[str, object]:
    settings = get_settings()
    if repository not in settings.coding_repositories:
        raise HTTPException(status_code=400, detail={"code": "unauthorized_repository"})
    service = DevelopmentPipelineStateService(
        RepositoryTruthService(settings.coding_repositories)
    )
    try:
        return service.inspect(
            repository=repository,
            pr_number=pr_number,
            spec_id=spec_id,
        )
    except PipelineStateInputError as exc:
        raise HTTPException(status_code=400, detail={"code": str(exc)}) from exc
