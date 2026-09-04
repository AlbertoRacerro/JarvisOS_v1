from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.core.config import get_settings
from app.modules.ai.jarvis_context import PRODUCTION_CAPABILITY_REGISTRY
from app.modules.ai.jarvis_context_models import JarvisCapabilityDescriptor
from app.modules.coding.actions import (
    CodingActionError,
    CodingActionsService,
    CodingInspectRequest,
    CodingSuggestModificationRequest,
)
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

for _capability in (
    JarvisCapabilityDescriptor(
        capability_id="coding.inspect",
        route_id="coding-repository",
        action_class="READ",
        label="Inspect exact Coding repository evidence",
    ),
    JarvisCapabilityDescriptor(
        capability_id="coding.inspect",
        route_id="coding-runtime",
        action_class="READ",
        label="Inspect exact Coding runtime evidence",
    ),
    JarvisCapabilityDescriptor(
        capability_id="coding.suggest-modification",
        route_id="coding-repository",
        action_class="PROPOSE",
        label="Suggest an exact-base repository modification",
    ),
):
    PRODUCTION_CAPABILITY_REGISTRY.register(_capability)


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


@router.post("/actions/inspect")
def coding_inspect(payload: CodingInspectRequest) -> dict[str, object]:
    settings = get_settings()
    if payload.repository not in settings.coding_repositories:
        return {"state": "refused", "reason": "missing_evidence"}
    service = CodingActionsService(RepositoryTruthService(settings.coding_repositories))
    try:
        return service.inspect(payload)
    except CodingActionError as exc:
        return {"state": "refused", "reason": exc.reason}


@router.post("/actions/suggest-modification")
def coding_suggest_modification(payload: CodingSuggestModificationRequest) -> dict[str, object]:
    settings = get_settings()
    if payload.repository not in settings.coding_repositories:
        return {"state": "refused", "reason": "missing_evidence"}
    service = CodingActionsService(RepositoryTruthService(settings.coding_repositories))
    return service.suggest_modification(payload)
