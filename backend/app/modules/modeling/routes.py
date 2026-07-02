import sqlite3

from fastapi import APIRouter, HTTPException

from app.modules.modeling.models import (
    AssumptionCreate,
    AssumptionRead,
    DecisionCreate,
    DecisionRead,
    ModelSpecCreate,
    ModelSpecRead,
    ParameterCreate,
    ParameterRead,
    RequirementCreate,
    RequirementRead,
    RequirementUpdate,
    SimulationRunCreate,
    SimulationRunRead,
)
from app.modules.modeling.service import (
    create_assumption,
    create_decision,
    create_model_spec,
    create_parameter,
    create_requirement,
    create_simulation_run,
    get_model_spec,
    get_requirement,
    list_assumptions,
    list_decisions,
    list_model_specs,
    list_parameters,
    list_requirements,
    list_simulation_runs,
    update_requirement,
)

router = APIRouter(tags=["modeling"])


def _domain_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, sqlite3.IntegrityError):
        return HTTPException(status_code=400, detail="Related record was not found.")
    return HTTPException(status_code=500, detail="Unexpected persistence error.")


@router.post("/workspaces/{workspace_id}/model-specs", response_model=ModelSpecRead, status_code=201)
def create_model_spec_endpoint(workspace_id: str, payload: ModelSpecCreate) -> ModelSpecRead:
    try:
        return create_model_spec(workspace_id, payload)
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _domain_error(exc) from exc


@router.get("/workspaces/{workspace_id}/model-specs", response_model=list[ModelSpecRead])
def list_model_specs_endpoint(workspace_id: str) -> list[ModelSpecRead]:
    try:
        return list_model_specs(workspace_id)
    except ValueError as exc:
        raise _domain_error(exc) from exc


@router.get("/model-specs/{model_spec_id}", response_model=ModelSpecRead)
def get_model_spec_endpoint(model_spec_id: str) -> ModelSpecRead:
    model_spec = get_model_spec(model_spec_id)
    if model_spec is None:
        raise HTTPException(status_code=404, detail="Model spec not found.")
    return model_spec


@router.post("/workspaces/{workspace_id}/assumptions", response_model=AssumptionRead, status_code=201)
def create_assumption_endpoint(workspace_id: str, payload: AssumptionCreate) -> AssumptionRead:
    try:
        return create_assumption(workspace_id, payload)
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _domain_error(exc) from exc


@router.get("/workspaces/{workspace_id}/assumptions", response_model=list[AssumptionRead])
def list_assumptions_endpoint(workspace_id: str) -> list[AssumptionRead]:
    try:
        return list_assumptions(workspace_id)
    except ValueError as exc:
        raise _domain_error(exc) from exc


@router.post("/workspaces/{workspace_id}/parameters", response_model=ParameterRead, status_code=201)
def create_parameter_endpoint(workspace_id: str, payload: ParameterCreate) -> ParameterRead:
    try:
        return create_parameter(workspace_id, payload)
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _domain_error(exc) from exc


@router.get("/workspaces/{workspace_id}/parameters", response_model=list[ParameterRead])
def list_parameters_endpoint(workspace_id: str) -> list[ParameterRead]:
    try:
        return list_parameters(workspace_id)
    except ValueError as exc:
        raise _domain_error(exc) from exc


@router.post("/workspaces/{workspace_id}/requirements", response_model=RequirementRead, status_code=201)
def create_requirement_endpoint(workspace_id: str, payload: RequirementCreate) -> RequirementRead:
    try:
        return create_requirement(workspace_id, payload)
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _domain_error(exc) from exc


@router.get("/workspaces/{workspace_id}/requirements", response_model=list[RequirementRead])
def list_requirements_endpoint(workspace_id: str) -> list[RequirementRead]:
    try:
        return list_requirements(workspace_id)
    except ValueError as exc:
        raise _domain_error(exc) from exc


@router.get("/requirements/{requirement_id}", response_model=RequirementRead)
def get_requirement_endpoint(requirement_id: str) -> RequirementRead:
    requirement = get_requirement(requirement_id)
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    return requirement


@router.patch("/requirements/{requirement_id}", response_model=RequirementRead)
def update_requirement_endpoint(requirement_id: str, payload: RequirementUpdate) -> RequirementRead:
    requirement = update_requirement(requirement_id, payload)
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    return requirement


@router.post("/workspaces/{workspace_id}/simulation-runs", response_model=SimulationRunRead, status_code=201)
def create_simulation_run_endpoint(workspace_id: str, payload: SimulationRunCreate) -> SimulationRunRead:
    try:
        return create_simulation_run(workspace_id, payload)
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _domain_error(exc) from exc


@router.get("/workspaces/{workspace_id}/simulation-runs", response_model=list[SimulationRunRead])
def list_simulation_runs_endpoint(workspace_id: str) -> list[SimulationRunRead]:
    try:
        return list_simulation_runs(workspace_id)
    except ValueError as exc:
        raise _domain_error(exc) from exc


@router.post("/workspaces/{workspace_id}/decisions", response_model=DecisionRead, status_code=201)
def create_decision_endpoint(workspace_id: str, payload: DecisionCreate) -> DecisionRead:
    try:
        return create_decision(workspace_id, payload)
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _domain_error(exc) from exc


@router.get("/workspaces/{workspace_id}/decisions", response_model=list[DecisionRead])
def list_decisions_endpoint(workspace_id: str) -> list[DecisionRead]:
    try:
        return list_decisions(workspace_id)
    except ValueError as exc:
        raise _domain_error(exc) from exc
