from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.modules.coding.repository_truth import RepositoryTruthService
from app.modules.coding.runtime_truth import (
    RuntimeSnapshot,
    observe_runtime_truth,
    startup_snapshot_unavailable,
)

router = APIRouter(prefix="/api/coding", tags=["coding"])


@router.get("/runtime-truth")
def runtime_truth(
    request: Request,
    repository: str,
    target_ref: str,
) -> dict[str, object]:
    settings = get_settings()
    startup = getattr(request.app.state, "coding_runtime_startup_snapshot", None)
    if not isinstance(startup, RuntimeSnapshot):
        startup = startup_snapshot_unavailable()
    service = RepositoryTruthService(settings.coding_repositories)
    result = observe_runtime_truth(
        repository=repository,
        target_ref=target_ref,
        configured_repositories=settings.coding_repositories,
        startup=startup,
        repository_truth=service,
    )
    return result.to_dict()
