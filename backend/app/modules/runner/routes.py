from fastapi import APIRouter, HTTPException

from app.modules.runner.models import (
    ModelImplementationCreate,
    ModelImplementationRead,
    RunArtifactRead,
    RunLogRead,
    RunnerJobCreate,
    RunnerJobCreateResponse,
    RunnerJobRunResponse,
    SimulationRunDetail,
)
from app.modules.runner.safety import RunnerSafetyError
from app.modules.runner.service import (
    create_model_implementation,
    create_runner_job,
    get_simulation_run_detail,
    list_model_implementations,
    list_run_artifacts,
    list_run_logs,
    run_runner_job,
)

router = APIRouter(tags=["runner"])


def _runner_error(exc: RunnerSafetyError) -> HTTPException:
    not_found = {
        "runner_workspace_not_found",
        "runner_model_spec_not_found",
        "runner_model_version_not_found",
        "runner_job_not_found",
        "runner_simulation_run_not_found",
    }
    conflicts = {"runner_job_not_queued"}
    status_code = 404 if exc.code in not_found else 409 if exc.code in conflicts else 400
    return HTTPException(status_code=status_code, detail={"code": exc.code, "message": exc.message})


@router.post(
    "/workspaces/{workspace_id}/model-implementations",
    response_model=ModelImplementationRead,
    status_code=201,
)
def create_model_implementation_endpoint(
    workspace_id: str,
    payload: ModelImplementationCreate,
) -> ModelImplementationRead:
    try:
        return create_model_implementation(workspace_id, payload)
    except RunnerSafetyError as exc:
        raise _runner_error(exc) from exc


@router.get("/workspaces/{workspace_id}/model-implementations", response_model=list[ModelImplementationRead])
def list_model_implementations_endpoint(workspace_id: str) -> list[ModelImplementationRead]:
    try:
        return list_model_implementations(workspace_id)
    except RunnerSafetyError as exc:
        raise _runner_error(exc) from exc


@router.post("/workspaces/{workspace_id}/runner-jobs", response_model=RunnerJobCreateResponse, status_code=201)
def create_runner_job_endpoint(workspace_id: str, payload: RunnerJobCreate) -> RunnerJobCreateResponse:
    try:
        return create_runner_job(workspace_id, payload)
    except RunnerSafetyError as exc:
        raise _runner_error(exc) from exc


@router.post("/runner-jobs/{runner_job_id}/run", response_model=RunnerJobRunResponse)
def run_runner_job_endpoint(runner_job_id: str) -> RunnerJobRunResponse:
    try:
        return run_runner_job(runner_job_id)
    except RunnerSafetyError as exc:
        raise _runner_error(exc) from exc


@router.get("/workspaces/{workspace_id}/simulation-runs/{simulation_run_id}", response_model=SimulationRunDetail)
def get_simulation_run_endpoint(workspace_id: str, simulation_run_id: str) -> SimulationRunDetail:
    try:
        return get_simulation_run_detail(workspace_id, simulation_run_id)
    except RunnerSafetyError as exc:
        raise _runner_error(exc) from exc


@router.get("/workspaces/{workspace_id}/simulation-runs/{simulation_run_id}/logs", response_model=list[RunLogRead])
def list_run_logs_endpoint(workspace_id: str, simulation_run_id: str) -> list[RunLogRead]:
    try:
        return list_run_logs(workspace_id, simulation_run_id)
    except RunnerSafetyError as exc:
        raise _runner_error(exc) from exc


@router.get(
    "/workspaces/{workspace_id}/simulation-runs/{simulation_run_id}/artifacts",
    response_model=list[RunArtifactRead],
)
def list_run_artifacts_endpoint(workspace_id: str, simulation_run_id: str) -> list[RunArtifactRead]:
    try:
        return list_run_artifacts(workspace_id, simulation_run_id)
    except RunnerSafetyError as exc:
        raise _runner_error(exc) from exc
