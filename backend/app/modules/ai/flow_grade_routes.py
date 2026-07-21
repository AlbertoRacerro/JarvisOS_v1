from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.modules.ai.flow_grade_contracts import (
    FlowGradeConflictError,
    FlowGradeContractError,
    FlowGradeNotFoundError,
)
from app.modules.ai.flow_grade_events import set_flow_grade, withdraw_flow_grade
from app.modules.ai.flow_grade_models import (
    FlowGradeEventRead,
    FlowGradeRead,
    FlowGradeSetRequest,
    FlowGradeWithdrawRequest,
)
from app.modules.ai.flow_grade_read import get_flow_grade_state

router = APIRouter(tags=["ai"])


@router.get("/flows/{flow_id}/grade", response_model=FlowGradeRead)
def read_flow_grade(flow_id: str) -> FlowGradeRead:
    try:
        return FlowGradeRead.model_validate(get_flow_grade_state(flow_id))
    except FlowGradeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FlowGradeConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except FlowGradeContractError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/flows/{flow_id}/grade", response_model=FlowGradeEventRead)
def write_flow_grade(
    flow_id: str,
    payload: FlowGradeSetRequest,
) -> FlowGradeEventRead:
    try:
        result = set_flow_grade(
            flow_id=flow_id,
            grade=payload.grade,
            expected_subject_version=payload.expected_subject_version,
            expected_flow_outcome_digest=payload.expected_flow_outcome_digest,
            expected_current_grade_event_id=payload.expected_current_grade_event_id,
            idempotency_key=payload.idempotency_key,
            reason_codes=payload.reason_codes,
            note=payload.note,
            source="operator_api",
        )
        return FlowGradeEventRead.model_validate(result)
    except FlowGradeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FlowGradeConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except FlowGradeContractError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/flows/{flow_id}/grade/withdraw", response_model=FlowGradeEventRead)
def withdraw_flow_grade_endpoint(
    flow_id: str,
    payload: FlowGradeWithdrawRequest,
) -> FlowGradeEventRead:
    try:
        result = withdraw_flow_grade(
            flow_id=flow_id,
            expected_subject_version=payload.expected_subject_version,
            expected_flow_outcome_digest=payload.expected_flow_outcome_digest,
            expected_current_grade_event_id=payload.expected_current_grade_event_id,
            idempotency_key=payload.idempotency_key,
            source="operator_api",
        )
        return FlowGradeEventRead.model_validate(result)
    except FlowGradeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FlowGradeConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except FlowGradeContractError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
