from __future__ import annotations

from dataclasses import asdict

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
from app.modules.coding.repository_truth import RepositoryTruthError, RepositoryTruthService
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


def _repository_service() -> RepositoryTruthService:
    return RepositoryTruthService(get_settings().coding_repositories)


def _repository_result(call: object) -> dict[str, object]:
    try:
        result = call()  # type: ignore[operator]
    except RepositoryTruthError as exc:
        status = 400
        if exc.code in {"authentication_required"}:
            status = 401
        elif exc.code in {"not_found"}:
            status = 404
        elif exc.code in {"rate_limited"}:
            status = 429
        elif exc.code in {"provider_unavailable", "timeout"}:
            status = 503
        raise HTTPException(
            status_code=status,
            detail={
                "code": exc.code,
                "partial": exc.partial,
                "metadata": exc.metadata,
            },
        ) from exc
    return asdict(result)


@router.get("/repository/ref")
def repository_ref(repository: str, ref: str) -> dict[str, object]:
    service = _repository_service()
    return _repository_result(lambda: service.repository_ref_truth(repository, ref))


@router.get("/repository/tree")
def repository_tree(repository: str, ref: str, path: str = "") -> dict[str, object]:
    service = _repository_service()
    return _repository_result(lambda: service.path_list(repository, ref, path))


@router.get("/repository/file")
def repository_file(repository: str, ref: str, path: str) -> dict[str, object]:
    service = _repository_service()
    return _repository_result(lambda: service.file_preview(repository, ref, path))


@router.get("/repository/search")
def repository_search(repository: str, ref: str, literal: str) -> dict[str, object]:
    service = _repository_service()
    return _repository_result(lambda: service.literal_search(repository, ref, literal))


@router.get("/repository/pull-request")
def repository_pull_request(repository: str, pr_number: int) -> dict[str, object]:
    service = _repository_service()
    return _repository_result(lambda: service.pull_request_truth(repository, pr_number))


@router.get("/repository/checks")
def repository_checks(
    repository: str,
    pr_number: int,
    expected_head_sha: str,
) -> dict[str, object]:
    service = _repository_service()
    return _repository_result(
        lambda: service.check_truth(
            repository,
            pr_number,
            expected_head_sha=expected_head_sha,
        )
    )


@router.get("/repository/reviews")
def repository_reviews(
    repository: str,
    pr_number: int,
    expected_head_sha: str,
) -> dict[str, object]:
    service = _repository_service()
    return _repository_result(
        lambda: service.review_truth(
            repository,
            pr_number,
            expected_head_sha=expected_head_sha,
        )
    )


@router.get("/repository/url")
def repository_url(
    repository: str,
    commit_sha: str | None = None,
    pr_number: int | None = None,
    path: str | None = None,
) -> dict[str, object]:
    service = _repository_service()
    return _repository_result(
        lambda: service.safe_github_url(
            repository,
            commit_sha=commit_sha,
            pr_number=pr_number,
            path=path,
        )
    )


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

    service = RuntimeTruthService(_repository_service())
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
    service = DevelopmentPipelineStateService(_repository_service())
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
    service = CodingActionsService(_repository_service())
    try:
        return service.inspect(payload)
    except CodingActionError as exc:
        return {"state": "refused", "reason": exc.reason}


@router.post("/actions/suggest-modification")
def coding_suggest_modification(payload: CodingSuggestModificationRequest) -> dict[str, object]:
    settings = get_settings()
    if payload.repository not in settings.coding_repositories:
        return {"state": "refused", "reason": "missing_evidence"}
    service = CodingActionsService(_repository_service())
    return service.suggest_modification(payload)
