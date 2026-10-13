"""Operator-facing Studio authoring routes."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.runner.origin import require_runner_origin
from app.modules.studio import service
from app.modules.studio.models import StudioCreate, StudioError, StudioUpdate, TestRequest

router = APIRouter(tags=["studio"])

_CATEGORIES = [
    {"id": "calculation", "label": "Calculation", "available": True, "reason": None},
    {"id": "steady_unit_operation", "label": "Steady unit operation", "available": False, "reason": "Process Studio flowsheet integration is planned."},
    {"id": "dynamic_model", "label": "Dynamic model", "available": False, "reason": "Time integration is not available in this slice."},
    {"id": "procedure", "label": "Procedure", "available": False, "reason": "Procedure authoring is planned."},
    {"id": "geometry", "label": "Geometry", "available": False, "reason": "CAD-as-code authoring is planned."},
    {"id": "optimization", "label": "Optimization", "available": False, "reason": "Optimization orchestration is not available."},
    {"id": "cfd_fem", "label": "CFD/FEM", "available": False, "reason": "A governed solver integration is not available."},
]


def _call(function, *args):
    try:
        return function(*args)
    except StudioError as exc:
        code = 404 if exc.code.endswith("not_found") else 409 if exc.code in {
            "studio_publish_report_required", "studio_no_published_version", "studio_artifact_hash_mismatch",
            "studio_draft_open", "studio_revision_required"
        } else 422
        raise HTTPException(status_code=code, detail={"code": exc.code, "message": exc.message}) from exc


@router.get("/studio/categories")
def categories() -> list[dict]:
    return _CATEGORIES


@router.post("/workspaces/{workspace_id}/studio/models", status_code=201)
def create_model(workspace_id: str, data: StudioCreate) -> dict:
    return _call(service.create, workspace_id, data)


@router.get("/workspaces/{workspace_id}/studio/models")
def list_models(workspace_id: str) -> list[dict]:
    return _call(service.list_models, workspace_id)


@router.get("/workspaces/{workspace_id}/studio/models/{model_spec_id}")
def get_model(workspace_id: str, model_spec_id: str) -> dict:
    return _call(service.get, workspace_id, model_spec_id)


@router.put("/workspaces/{workspace_id}/studio/models/{model_spec_id}")
def save_model(workspace_id: str, model_spec_id: str, data: StudioUpdate) -> dict:
    return _call(service.update, workspace_id, model_spec_id, data)


@router.post("/workspaces/{workspace_id}/studio/models/{model_spec_id}/test", dependencies=[Depends(require_runner_origin)])
def test_model(workspace_id: str, model_spec_id: str, data: TestRequest) -> dict:
    return _call(service.test, workspace_id, model_spec_id, data)


@router.post("/workspaces/{workspace_id}/studio/models/{model_spec_id}/publish", dependencies=[Depends(require_runner_origin)])
def publish_model(workspace_id: str, model_spec_id: str) -> dict:
    return _call(service.publish, workspace_id, model_spec_id)


@router.post("/workspaces/{workspace_id}/studio/models/{model_spec_id}/revise")
def revise_model(workspace_id: str, model_spec_id: str) -> dict:
    return _call(service.revise, workspace_id, model_spec_id)


@router.get("/workspaces/{workspace_id}/studio/library")
def library(workspace_id: str) -> list[dict]:
    return _call(service.library, workspace_id)

