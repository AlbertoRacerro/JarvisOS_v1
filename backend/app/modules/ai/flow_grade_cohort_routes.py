from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.modules.ai.flow_grade_cohort_models import FlowGradeCohortRead
from app.modules.ai.flow_grade_cohorts import get_flow_grade_cohort
from app.modules.ai.flow_grade_contracts import FlowGradeContractError

router = APIRouter(tags=["ai"])


@router.get("/grade-cohorts", response_model=FlowGradeCohortRead)
def read_flow_grade_cohort(
    workspace_id: str | None = None,
    task_kind: str | None = None,
    limit: int = Query(default=1000, ge=1, le=5000),
) -> FlowGradeCohortRead:
    try:
        return get_flow_grade_cohort(
            workspace_id=workspace_id,
            task_kind=task_kind,
            limit=limit,
        )
    except (FlowGradeContractError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
